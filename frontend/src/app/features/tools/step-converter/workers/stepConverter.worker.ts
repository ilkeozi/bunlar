import {
  ConversionError,
  ValidationError,
  createConverter,
  injectAssetExtrasIntoGlb,
  type ConvertBufferResult,
  type InputFormat,
  type OutputFormat,
} from 'opencascade-convert/browser';

import { strToU8, zipSync } from 'fflate';

type TriangulatePayload = {
  linearDeflection?: number;
  angularDeflection?: number;
  relative?: boolean;
  parallel?: boolean;
};

type WorkerStage = 'parsing' | 'meshing' | 'writing' | 'metadata' | 'packaging';

export type StepConverterErrorCode =
  | 'FILE_TOO_LARGE'
  | 'UNSUPPORTED_EXTENSION'
  | 'INVALID_STEP'
  | 'UNSUPPORTED_STEP_CONTENT'
  | 'UNITS_SCALE_MISMATCH'
  | 'WASM_LOAD_FAILED'
  | 'CONVERSION_FAILED'
  | 'METADATA_FAILED'
  | 'GLB_PATCH_FAILED'
  | 'ZIP_FAILED'
  | 'OUT_OF_MEMORY';

export type StepConverterError = {
  code: StepConverterErrorCode;
  message: string;
  detail?: Record<string, unknown>;
};

type ConversionWarning = {
  code: string;
  message: string;
  detail?: Record<string, unknown>;
};

type MeshStats = {
  triangles: number;
  meshCount: number;
  nodeCount: number;
  primitiveCount: number;
  nodesWithMeshCount: number;
  primitivesWithPositionCount: number;
};

const TRIANGLE_EXPLOSION_THRESHOLDS = {
  MAX_TRIANGLES: 5_000_000,
  MAX_PRIMITIVES: 50_000,
} as const;

function isTriangleExplosion(stats: MeshStats) {
  return (
    stats.triangles > TRIANGLE_EXPLOSION_THRESHOLDS.MAX_TRIANGLES ||
    stats.primitiveCount > TRIANGLE_EXPLOSION_THRESHOLDS.MAX_PRIMITIVES
  );
}

type WorkerStartRequest = {
  type: 'START';
  id: number;
  filename: string;
  fileBytes: ArrayBuffer;
  triangulate: TriangulatePayload;
};

type WorkerProgress = {
  type: 'PROGRESS';
  id: number;
  stage: WorkerStage;
  progress?: number;
};

type WorkerDone = {
  type: 'DONE';
  id: number;
  bundleName: string;
  bundleBytes: ArrayBuffer;
  meshStats?: MeshStats;
  conversionWarnings?: ConversionWarning[];
};

type WorkerError = {
  type: 'ERROR';
  id: number;
  error: StepConverterError;
};

type WorkerRequest = {
  id: number;
  input: ArrayBuffer;
  inputFormat: InputFormat;
  outputFormat: OutputFormat;
  triangulate: TriangulatePayload;
  includeBom: boolean;
  includeNodeMap: boolean;
};

type WorkerSuccess =
  | {
      id: number;
      ok: true;
      outputFormat: 'glb' | 'obj';
      data: ArrayBuffer;
      bom?: unknown;
      nodeMap?: unknown;
    }
  | {
      id: number;
      ok: true;
      outputFormat: 'gltf';
      gltf: ArrayBuffer;
      bin: ArrayBuffer;
      bom?: unknown;
      nodeMap?: unknown;
    };

type WorkerFailure = {
  id: number;
  ok: false;
  error: string;
};

const converterPromise = createConverter();

function toTransferBuffer(data: Uint8Array) {
  // Ensure we always transfer an ArrayBuffer (not a SharedArrayBuffer).
  const out = new Uint8Array(data.byteLength);
  out.set(data);
  return out.buffer;
}

function mapResult(
  result: ConvertBufferResult,
  bom?: unknown,
  nodeMap?: unknown
): [WorkerSuccess, ArrayBuffer[]] {
  if (result.outputFormat === 'glb') {
    const data = toTransferBuffer(result.glb);
    return [
      { id: 0, ok: true, outputFormat: 'glb', data, bom, nodeMap },
      [data],
    ];
  }
  if (result.outputFormat === 'obj') {
    const data = toTransferBuffer(result.obj);
    return [
      { id: 0, ok: true, outputFormat: 'obj', data, bom, nodeMap },
      [data],
    ];
  }
  const gltf = toTransferBuffer(result.gltf);
  const bin = toTransferBuffer(result.bin);
  return [
    { id: 0, ok: true, outputFormat: 'gltf', gltf, bin, bom, nodeMap },
    [gltf, bin],
  ];
}

function baseNameFromFilename(filename: string) {
  const clean = filename.split('/').pop() ?? filename;
  return clean.replace(/\.[^/.]+$/, '') || 'conversion';
}

function approxEqual(a: number, b: number, epsilon = 1e-9) {
  return Math.abs(a - b) <= epsilon;
}

function unitNameFromScale(scaleToMeters: number) {
  if (approxEqual(scaleToMeters, 1)) return 'm';
  if (approxEqual(scaleToMeters, 0.001)) return 'mm';
  if (approxEqual(scaleToMeters, 0.01)) return 'cm';
  if (approxEqual(scaleToMeters, 0.0254)) return 'in';
  if (approxEqual(scaleToMeters, 0.3048)) return 'ft';
  return 'unknown';
}

function readInputUnitScaleToMeters(
  oc: any,
  docHandle: any
): {
  scaleToMeters: number;
  source: string;
} {
  const doc = docHandle?.get ? docHandle.get() : docHandle;
  const tool = oc?.XCAFDoc_DocumentTool;
  if (!tool) {
    return { scaleToMeters: 1, source: 'unknown' };
  }

  const candidates = ['GetLengthUnit', 'GetLengthUnit_1', 'GetLengthUnit_2'];
  for (const key of candidates) {
    const fn = tool[key];
    if (typeof fn !== 'function') {
      continue;
    }
    try {
      const value = fn(doc);
      if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
        return { scaleToMeters: value, source: `XCAFDoc_DocumentTool.${key}` };
      }
    } catch {
      // try next
    }
  }

  return { scaleToMeters: 1, source: 'unknown' };
}

function applyLengthUnitConversionToWriter(writer: any, scaleToMeters: number) {
  // Best-effort. API availability depends on OpenCascade.js bindings.
  try {
    const maybeConv =
      typeof writer.ChangeCoordinateSystemConverter === 'function'
        ? writer.ChangeCoordinateSystemConverter()
        : null;
    const conv = maybeConv ?? null;
    if (!conv) {
      return;
    }

    if (typeof conv.SetInputLengthUnit === 'function') {
      conv.SetInputLengthUnit(scaleToMeters);
    }
    if (typeof conv.SetOutputLengthUnit === 'function') {
      conv.SetOutputLengthUnit(1.0);
    }
    if (typeof writer.SetCoordinateSystemConverter === 'function') {
      writer.SetCoordinateSystemConverter(conv);
    }
  } catch {
    // ignore
  }
}

function parseGlbJson(glb: Uint8Array) {
  const GLB_HEADER_LENGTH = 12;
  const GLB_CHUNK_HEADER_LENGTH = 8;
  const GLB_JSON_CHUNK = 0x4e4f534a;
  if (glb.byteLength < GLB_HEADER_LENGTH + GLB_CHUNK_HEADER_LENGTH) {
    throw new Error('Invalid GLB: truncated header');
  }
  if (
    !(glb[0] === 0x67 && glb[1] === 0x6c && glb[2] === 0x54 && glb[3] === 0x46)
  ) {
    throw new Error('Invalid GLB: invalid magic');
  }
  const view = new DataView(glb.buffer, glb.byteOffset, glb.byteLength);
  let offset = GLB_HEADER_LENGTH;
  while (offset + GLB_CHUNK_HEADER_LENGTH <= glb.byteLength) {
    const chunkLength = view.getUint32(offset, true);
    const chunkType = view.getUint32(offset + 4, true);
    const chunkStart = offset + GLB_CHUNK_HEADER_LENGTH;
    const chunkEnd = chunkStart + chunkLength;
    if (chunkEnd > glb.byteLength) {
      throw new Error('Invalid GLB: truncated chunk');
    }
    if (chunkType === GLB_JSON_CHUNK) {
      const jsonText = new TextDecoder('utf-8').decode(
        glb.subarray(chunkStart, chunkEnd)
      );
      return JSON.parse(jsonText);
    }
    offset = chunkEnd;
  }
  throw new Error('Invalid GLB: missing JSON chunk');
}

function parseGlbBin(glb: Uint8Array) {
  const GLB_HEADER_LENGTH = 12;
  const GLB_CHUNK_HEADER_LENGTH = 8;
  const GLB_BIN_CHUNK = 0x004e4942;
  const view = new DataView(glb.buffer, glb.byteOffset, glb.byteLength);
  let offset = GLB_HEADER_LENGTH;
  while (offset + GLB_CHUNK_HEADER_LENGTH <= glb.byteLength) {
    const chunkLength = view.getUint32(offset, true);
    const chunkType = view.getUint32(offset + 4, true);
    const chunkStart = offset + GLB_CHUNK_HEADER_LENGTH;
    const chunkEnd = chunkStart + chunkLength;
    if (chunkEnd > glb.byteLength) {
      return null;
    }
    if (chunkType === GLB_BIN_CHUNK) {
      return glb.subarray(chunkStart, chunkEnd);
    }
    offset = chunkEnd;
  }
  return null;
}

function computeBoundsMeters(glb: Uint8Array) {
  const gltf = parseGlbJson(glb) as any;
  if (!gltf || !Array.isArray(gltf.meshes) || !Array.isArray(gltf.accessors)) {
    throw new Error('Invalid GLB: missing meshes/accessors');
  }

  const accessors = gltf.accessors as any[];
  const meshes = gltf.meshes as any[];

  const mins = [
    Number.POSITIVE_INFINITY,
    Number.POSITIVE_INFINITY,
    Number.POSITIVE_INFINITY,
  ];
  const maxs = [
    Number.NEGATIVE_INFINITY,
    Number.NEGATIVE_INFINITY,
    Number.NEGATIVE_INFINITY,
  ];

  const positionAccessorIndices = new Set<number>();
  meshes.forEach((mesh) => {
    (mesh?.primitives ?? []).forEach((prim: any) => {
      const idx = prim?.attributes?.POSITION;
      if (typeof idx === 'number') {
        positionAccessorIndices.add(idx);
      }
    });
  });

  const updateFromMinMax = (min: any, max: any) => {
    if (
      !Array.isArray(min) ||
      !Array.isArray(max) ||
      min.length < 3 ||
      max.length < 3
    ) {
      return false;
    }
    for (let i = 0; i < 3; i += 1) {
      const a = Number(min[i]);
      const b = Number(max[i]);
      if (!Number.isFinite(a) || !Number.isFinite(b)) {
        return false;
      }
      mins[i] = Math.min(mins[i], a);
      maxs[i] = Math.max(maxs[i], b);
    }
    return true;
  };

  let usedAny = false;
  for (const accessorIndex of positionAccessorIndices) {
    const accessor = accessors[accessorIndex];
    if (accessor && updateFromMinMax(accessor.min, accessor.max)) {
      usedAny = true;
    }
  }

  if (!usedAny) {
    // Fallback: compute bounds by reading BIN data.
    const bin = parseGlbBin(glb);
    if (!bin || !Array.isArray(gltf.bufferViews)) {
      throw new Error('Invalid GLB: missing BIN/bufferViews for bounds');
    }
    const bufferViews = gltf.bufferViews as any[];
    const binView = new DataView(bin.buffer, bin.byteOffset, bin.byteLength);

    for (const accessorIndex of positionAccessorIndices) {
      const accessor = accessors[accessorIndex];
      if (
        !accessor ||
        accessor.type !== 'VEC3' ||
        accessor.componentType !== 5126
      ) {
        continue;
      }
      const bv = bufferViews[accessor.bufferView];
      if (!bv) continue;
      const bvOffset = Number(bv.byteOffset ?? 0);
      const accOffset = Number(accessor.byteOffset ?? 0);
      const start = bvOffset + accOffset;
      const count = Number(accessor.count ?? 0);
      const stride = Number(bv.byteStride ?? 12);
      for (let i = 0; i < count; i += 1) {
        const off = start + i * stride;
        if (off + 12 > binView.byteLength) break;
        const x = binView.getFloat32(off + 0, true);
        const y = binView.getFloat32(off + 4, true);
        const z = binView.getFloat32(off + 8, true);
        mins[0] = Math.min(mins[0], x);
        mins[1] = Math.min(mins[1], y);
        mins[2] = Math.min(mins[2], z);
        maxs[0] = Math.max(maxs[0], x);
        maxs[1] = Math.max(maxs[1], y);
        maxs[2] = Math.max(maxs[2], z);
        usedAny = true;
      }
    }
  }

  if (
    !usedAny ||
    !mins.every(Number.isFinite) ||
    !maxs.every(Number.isFinite)
  ) {
    throw new Error('Failed to compute bounds');
  }
  return {
    min: mins as [number, number, number],
    max: maxs as [number, number, number],
  };
}

function maxDimension(bounds: {
  min: [number, number, number];
  max: [number, number, number];
}) {
  const dx = bounds.max[0] - bounds.min[0];
  const dy = bounds.max[1] - bounds.min[1];
  const dz = bounds.max[2] - bounds.min[2];
  return Math.max(Math.abs(dx), Math.abs(dy), Math.abs(dz));
}

function extractOcafEntry(name: string) {
  const matches = name.match(/\b\d+(?::\d+)+\b/g);
  return matches ? matches[matches.length - 1] : null;
}

function cleanGltfNodeName(name: string) {
  const trimmed = name.trim();
  if (!trimmed) {
    return '';
  }
  // Common pattern when using RWMesh name formats: "Part Name [0:1:1:1:3]".
  const parts = trimmed.split(/\s*\[/);
  if (parts.length === 1) {
    return trimmed;
  }

  const cleaned: string[] = [parts[0].trim()];
  for (let index = 1; index < parts.length; index += 1) {
    const segment = parts[index];
    const closeIndex = segment.indexOf(']');
    if (closeIndex === -1) {
      continue;
    }
    const inside = segment.slice(0, closeIndex).trim();
    if (!inside) {
      continue;
    }
    // Skip raw OCAF entries and other low-signal tags.
    if (/\b\d+(?::\d+)+\b/.test(inside)) {
      continue;
    }
    if (/NAUO\d+/i.test(inside)) {
      continue;
    }
    cleaned.push(`[${inside}]`);
  }

  const result = cleaned.filter(Boolean).join(' ').replace(/\s+/g, ' ').trim();
  return result || trimmed;
}

function buildPrettyNameOverridesFromGlb(glb: Uint8Array) {
  const gltf = parseGlbJson(glb) as any;
  const nodes = Array.isArray(gltf?.nodes) ? (gltf.nodes as any[]) : [];
  const overrides = new Map<string, string>();
  nodes.forEach((node) => {
    if (!node?.name || typeof node.name !== 'string') {
      return;
    }
    const entry = extractOcafEntry(node.name);
    if (!entry || overrides.has(entry)) {
      return;
    }
    const cleaned = cleanGltfNodeName(node.name);
    if (cleaned && cleaned !== entry) {
      overrides.set(entry, cleaned);
    }
  });
  return overrides;
}

function buildGltfNodeIndexByOcafEntry(glb: Uint8Array) {
  const gltf = parseGlbJson(glb) as any;
  const nodes = Array.isArray(gltf?.nodes) ? (gltf.nodes as any[]) : [];
  const map = new Map<
    string,
    { gltfNodeIndex: number; gltfMeshIndex?: number }
  >();
  nodes.forEach((node, index) => {
    if (!node?.name || typeof node.name !== 'string') {
      return;
    }
    const entry = extractOcafEntry(node.name);
    if (!entry) {
      return;
    }
    if (map.has(entry)) {
      return;
    }
    const meshIndex = typeof node.mesh === 'number' ? node.mesh : undefined;
    map.set(entry, { gltfNodeIndex: index, gltfMeshIndex: meshIndex });
  });
  return map;
}

function buildAssemblyTree(nodeMap: {
  roots: string[];
  nodes: Record<string, any>;
}) {
  const visit = (id: string): any => {
    const node = nodeMap.nodes[id];
    if (!node) return null;
    return {
      id: node.id,
      name: node.name,
      children: (node.childrenIds ?? node.children ?? [])
        .map((childId: string) => visit(childId))
        .filter(Boolean),
    };
  };
  return nodeMap.roots.map((id) => visit(id)).filter(Boolean);
}

function isProbablyOutOfMemory(error: unknown) {
  if (!error) return false;
  const message =
    error instanceof Error
      ? error.message
      : typeof error === 'string'
      ? error
      : '';
  return /out of memory|memory access out of bounds|cannot allocate|allocation failed/i.test(
    message
  );
}

function isProbablyWasmLoadFailure(error: unknown) {
  if (!error) return false;
  const message =
    error instanceof Error
      ? error.message
      : typeof error === 'string'
      ? error
      : '';
  return /wasm|webassembly|instantiate|compile|fetch/i.test(message);
}

function isProbablyUnsupportedStepContentMessage(message: string) {
  return /no shapes|no supported|no solids|no geometry|empty model|empty shape/i.test(
    message
  );
}

function normalizeWorkerError(error: unknown): StepConverterError {
  if (isProbablyOutOfMemory(error)) {
    return {
      code: 'OUT_OF_MEMORY',
      message: 'Out of memory during conversion.',
    };
  }

  if (isProbablyWasmLoadFailure(error)) {
    return {
      code: 'WASM_LOAD_FAILED',
      message: 'Failed to load the conversion engine.',
    };
  }

  if (error instanceof ValidationError) {
    if (isProbablyUnsupportedStepContentMessage(error.message)) {
      return {
        code: 'UNSUPPORTED_STEP_CONTENT',
        message: 'This STEP file contains no supported solids/assemblies.',
      };
    }
    return { code: 'CONVERSION_FAILED', message: error.message };
  }

  if (error instanceof ConversionError) {
    if (/could not read/i.test(error.message)) {
      return { code: 'INVALID_STEP', message: 'Invalid or corrupt STEP file.' };
    }
    if (isProbablyUnsupportedStepContentMessage(error.message)) {
      return {
        code: 'UNSUPPORTED_STEP_CONTENT',
        message: 'This STEP file contains no supported solids/assemblies.',
      };
    }
    return { code: 'CONVERSION_FAILED', message: error.message };
  }

  const message =
    error instanceof Error
      ? error.message
      : typeof error === 'string'
      ? error
      : 'Conversion failed.';
  if (/could not read/i.test(message)) {
    return { code: 'INVALID_STEP', message: 'Invalid or corrupt STEP file.' };
  }
  if (isProbablyUnsupportedStepContentMessage(message)) {
    return {
      code: 'UNSUPPORTED_STEP_CONTENT',
      message: 'This STEP file contains no supported solids/assemblies.',
    };
  }
  return { code: 'CONVERSION_FAILED', message };
}

function summarizeGlbGeometry(glb: Uint8Array) {
  const gltf = parseGlbJson(glb) as any;
  const accessors = Array.isArray(gltf?.accessors)
    ? (gltf.accessors as any[])
    : [];
  const meshes = Array.isArray(gltf?.meshes) ? (gltf.meshes as any[]) : [];
  const nodes = Array.isArray(gltf?.nodes) ? (gltf.nodes as any[]) : [];

  let triangles = 0;
  let primitiveCount = 0;
  let primitivesWithPositionCount = 0;

  meshes.forEach((mesh) => {
    (mesh?.primitives ?? []).forEach((prim: any) => {
      primitiveCount += 1;

      const posAccessorIndex = prim?.attributes?.POSITION;
      if (typeof posAccessorIndex === 'number') {
        primitivesWithPositionCount += 1;
      }

      // glTF default is TRIANGLES (4) when mode is omitted.
      const mode = typeof prim?.mode === 'number' ? prim.mode : 4;
      if (mode !== 4) {
        return;
      }

      if (typeof prim?.indices === 'number') {
        const accessor = accessors[prim.indices];
        const count = Number(accessor?.count);
        if (Number.isFinite(count) && count > 0) {
          triangles += Math.floor(count / 3);
        }
        return;
      }

      if (typeof posAccessorIndex === 'number') {
        const accessor = accessors[posAccessorIndex];
        const count = Number(accessor?.count);
        if (Number.isFinite(count) && count > 0) {
          triangles += Math.floor(count / 3);
        }
      }
    });
  });

  const nodesWithMeshCount = nodes.filter(
    (node) => typeof node?.mesh === 'number'
  ).length;

  const stats: MeshStats = {
    triangles,
    meshCount: meshes.length,
    nodeCount: nodes.length,
    primitiveCount,
    nodesWithMeshCount,
    primitivesWithPositionCount,
  };
  return stats;
}

async function convertStepDocToGlb(params: {
  converter: any;
  docHandle: any;
  triangulate: TriangulatePayload;
  nameFormat?: 'productOrInstance' | 'productAndInstanceAndOcaf';
}) {
  const converter = params.converter;
  const docHandle = params.docHandle;
  const oc = (converter as any).oc;

  converter.triangulate(docHandle.get(), params.triangulate);

  // Write GLB directly so we can attempt unit conversion (best-effort).
  const pathInternal = './output.glb';
  const progress = new oc.Message_ProgressRange_1();
  const file = new oc.TCollection_AsciiString_2(pathInternal);
  const writer = new oc.RWGltf_CafWriter(file, true);
  if (typeof writer.SetMergeFaces === 'function') {
    writer.SetMergeFaces(true);
  }
  const formatKey =
    params.nameFormat === 'productAndInstanceAndOcaf'
      ? 'RWMesh_NameFormat_ProductAndInstanceAndOcaf'
      : 'RWMesh_NameFormat_ProductOrInstance';
  const nameFormat = oc.RWMesh_NameFormat?.[formatKey];
  if (nameFormat && typeof writer.SetNodeNameFormat === 'function') {
    writer.SetNodeNameFormat(nameFormat);
    if (typeof writer.SetMeshNameFormat === 'function') {
      writer.SetMeshNameFormat(nameFormat);
    }
  }

  const { scaleToMeters } = readInputUnitScaleToMeters(oc, docHandle);
  applyLengthUnitConversionToWriter(writer, scaleToMeters);

  const map = new oc.TColStd_IndexedDataMapOfStringString_1();
  writer.Perform_2(docHandle, map, progress);
  const data =
    oc.FS.analyzePath(pathInternal).exists && oc.FS.readFile(pathInternal);
  if (data) {
    oc.FS.unlink(pathInternal);
  }
  if (!data) {
    throw new ConversionError('Failed to generate GLB output.');
  }
  return data;
}

async function handleStartMessage(message: WorkerStartRequest) {
  const postProgress = (stage: WorkerStage, progress?: number) => {
    const update: WorkerProgress = { type: 'PROGRESS', id: message.id, stage };
    if (typeof progress === 'number') {
      update.progress = progress;
    }
    (self as DedicatedWorkerGlobalScope).postMessage(update);
  };

  try {
    const inputFormat: InputFormat = 'step';

    postProgress('parsing');
    const converter = await converterPromise;
    const docHandle = converter.readBuffer(
      new Uint8Array(message.fileBytes),
      inputFormat,
      {
        preserveNames: true,
        preserveColors: true,
        preserveLayers: true,
        preserveMaterials: true,
      }
    );

    // Detect supported container but no supported solids/assemblies.
    const nodeMapRaw = converter.createNodeMap(docHandle) as any;
    const rootCount = Array.isArray(nodeMapRaw?.roots)
      ? nodeMapRaw.roots.length
      : 0;
    const nodeCount = nodeMapRaw?.nodes
      ? Object.keys(nodeMapRaw.nodes as Record<string, unknown>).length
      : 0;
    if (rootCount === 0 || nodeCount === 0) {
      throw Object.assign(
        new Error('This STEP file contains no supported solids/assemblies.'),
        {
          __code: 'UNSUPPORTED_STEP_CONTENT',
          detail: { rootCount, nodeCount },
        }
      );
    }

    postProgress('meshing');
    postProgress('writing');
    const conversionWarnings: ConversionWarning[] = [];
    const triangulateOriginal = message.triangulate ?? {};
    const linearDeflection0 = triangulateOriginal.linearDeflection ?? 1;
    const angularDeflection0 = triangulateOriginal.angularDeflection ?? 0.5;

    if (triangulateOriginal.relative === true) {
      conversionWarnings.push({
        code: 'mesh/relative-forced-false',
        message:
          'Relative deflection was disabled to ensure absolute tessellation.',
        detail: {
          triangulateOriginal,
          triangulateForced: {
            ...triangulateOriginal,
            relative: false,
          },
        },
      });
    }

    const triangulateForAttempt = (attempt: number): TriangulatePayload => {
      if (attempt === 0) {
        return {
          linearDeflection: linearDeflection0,
          angularDeflection: angularDeflection0,
          relative: false,
          parallel: triangulateOriginal.parallel,
        };
      }

      if (attempt === 1) {
        return {
          linearDeflection: linearDeflection0 * 2,
          angularDeflection: Math.min(1.0, angularDeflection0 * 1.4),
          relative: false,
          parallel: triangulateOriginal.parallel,
        };
      }

      return {
        linearDeflection: linearDeflection0 * 4,
        angularDeflection: Math.min(1.2, angularDeflection0 * 1.8),
        relative: false,
        parallel: triangulateOriginal.parallel,
      };
    };

    let glb: Uint8Array | null = null;
    let meshStats: MeshStats | null = null;
    let triangulateUsed: TriangulatePayload | null = null;

    for (let attempt = 0; attempt < 3; attempt += 1) {
      triangulateUsed = triangulateForAttempt(attempt);
      const candidate = await convertStepDocToGlb({
        converter,
        docHandle,
        triangulate: triangulateUsed,
        nameFormat: 'productAndInstanceAndOcaf',
      });

      const stats = summarizeGlbGeometry(candidate);
      glb = candidate;
      meshStats = stats;

      if (!isTriangleExplosion(stats)) {
        break;
      }

      if (attempt < 2) {
        conversionWarnings.push({
          code: 'mesh/triangle-explosion-retry',
          message: `Triangle explosion detected on attempt ${attempt}; meshing was coarsened and retried.`,
          detail: {
            attempt,
            thresholds: TRIANGLE_EXPLOSION_THRESHOLDS,
            meshStats: stats,
            triangulateUsed,
          },
        });
        continue;
      }

      conversionWarnings.push({
        code: 'mesh/triangle-explosion-unresolved',
        message:
          'Triangle explosion thresholds were exceeded after the final attempt.',
        detail: {
          attempt,
          thresholds: TRIANGLE_EXPLOSION_THRESHOLDS,
          meshStats: stats,
          triangulateUsed,
        },
      });
      break;
    }

    if (!glb || !meshStats) {
      throw new ConversionError('Failed to generate GLB output.');
    }

    if (
      meshStats.meshCount === 0 ||
      meshStats.primitivesWithPositionCount === 0
    ) {
      throw Object.assign(
        new Error('This STEP file contains no supported solids/assemblies.'),
        {
          __code: 'UNSUPPORTED_STEP_CONTENT',
          detail: meshStats,
        }
      );
    }

    const base = baseNameFromFilename(message.filename);

    postProgress('metadata');
    const oc = (converter as any).oc;
    const bomRaw = converter.createBom(docHandle);
    const gltfNodeIndexByEntry = buildGltfNodeIndexByOcafEntry(glb);
    const prettyNamesByEntry = buildPrettyNameOverridesFromGlb(glb);

    const entryToNodeId = new Map<string, string>();
    Object.values(nodeMapRaw.nodes as Record<string, any>).forEach(
      (node: any) => {
        if (node?.labelEntry && typeof node.labelEntry === 'string') {
          entryToNodeId.set(node.labelEntry, node.id);
        }
      }
    );

    const usedGltfNodeIndices = new Set<number>();
    const nodes: Record<string, any> = {};
    for (const [nodeId, node] of Object.entries(
      nodeMapRaw.nodes as Record<string, any>
    )) {
      const mapping =
        typeof node.labelEntry === 'string'
          ? gltfNodeIndexByEntry.get(node.labelEntry)
          : undefined;
      if (!mapping) {
        throw Object.assign(
          new Error(`Missing glTF mapping for node ${nodeId}`),
          {
            __code: 'METADATA_FAILED',
          }
        );
      }
      if (usedGltfNodeIndices.has(mapping.gltfNodeIndex)) {
        throw Object.assign(
          new Error(
            `Duplicate glTF node mapping for index ${mapping.gltfNodeIndex}`
          ),
          {
            __code: 'METADATA_FAILED',
          }
        );
      }
      usedGltfNodeIndices.add(mapping.gltfNodeIndex);
      nodes[nodeId] = {
        id: node.id,
        name:
          (typeof node.labelEntry === 'string'
            ? prettyNamesByEntry.get(node.labelEntry)
            : undefined) || node.name,
        productId: node.productId,
        parentId: node.parentId ?? undefined,
        childrenIds: Array.isArray(node.children) ? node.children : [],
        gltfNodeIndex: mapping.gltfNodeIndex,
        gltfMeshIndex: mapping.gltfMeshIndex,
      };
    }

    const prettyNameByProductId = new Map<string, string>();
    Object.values(nodes).forEach((node: any) => {
      if (
        node &&
        typeof node.productId === 'string' &&
        node.productId.length > 0 &&
        typeof node.name === 'string' &&
        node.name.length > 0 &&
        !prettyNameByProductId.has(node.productId)
      ) {
        prettyNameByProductId.set(node.productId, node.name);
      }
    });

    const { scaleToMeters, source: inputUnitSource } =
      readInputUnitScaleToMeters(oc, docHandle);
    const inputLengthUnit = unitNameFromScale(scaleToMeters);

    const boundsMeters = computeBoundsMeters(glb);

    const maxDim = maxDimension(boundsMeters);
    const maxDimUnscaled = scaleToMeters > 0 ? maxDim / scaleToMeters : maxDim;
    const suspicious = maxDim > 0 && (maxDim < 1e-4 || maxDim > 1e4);
    const unscaledLooksPlausible =
      maxDimUnscaled >= 1e-4 && maxDimUnscaled <= 1e4;
    const differsByThousand =
      Math.abs(Math.log10(1 / (scaleToMeters || 1))) > 2.8;
    if (suspicious && unscaledLooksPlausible && differsByThousand) {
      const mismatch: StepConverterError = {
        code: 'UNITS_SCALE_MISMATCH',
        message: 'Units scale looks off by ~1000x.',
        detail: {
          maxDimensionMeters: maxDim,
          inputScaleToMeters: scaleToMeters,
        },
      };
      const response: WorkerError = {
        type: 'ERROR',
        id: message.id,
        error: mismatch,
      };
      (self as DedicatedWorkerGlobalScope).postMessage(response);
      return;
    }

    const metadata = {
      schemaVersion: 'bunlar-step-converter@1',
      meshStats,
      conversionWarnings,
      assemblyTree: buildAssemblyTree({ roots: nodeMapRaw.roots, nodes }),
      nodeMap: {
        roots: nodeMapRaw.roots,
        nodes,
      },
      bom: Array.isArray((bomRaw as any)?.items)
        ? (bomRaw as any).items.map((item: any) => ({
            name:
              (typeof item.productId === 'string'
                ? prettyNameByProductId.get(item.productId)
                : undefined) ||
              item.productName ||
              item.productId ||
              'Unknown',
            quantity: item.quantity ?? 0,
            productId: item.productId,
            kind: item.kind,
          }))
        : [],
      units: {
        inputLengthUnit,
        inputUnitSource,
        outputLengthUnit: 'm',
        scaleToMeters,
      },
      boundsMeters,
    };

    let patchedGlb: Uint8Array;
    try {
      patchedGlb = injectAssetExtrasIntoGlb(glb, {
        bunlarStepConverter: metadata,
      });
    } catch (error) {
      const response: WorkerError = {
        type: 'ERROR',
        id: message.id,
        error: {
          code: 'GLB_PATCH_FAILED',
          message: 'Failed to embed metadata into GLB.',
          detail: {
            error: error instanceof Error ? error.message : String(error),
          },
        },
      };
      (self as DedicatedWorkerGlobalScope).postMessage(response);
      return;
    }

    postProgress('packaging');
    let zipBytes: Uint8Array;
    try {
      zipBytes = zipSync(
        {
          [`${base}.glb`]: patchedGlb,
          [`${base}.metadata.json`]: strToU8(JSON.stringify(metadata)),
        },
        { level: 1 }
      );
    } catch (error) {
      const response: WorkerError = {
        type: 'ERROR',
        id: message.id,
        error: {
          code: 'ZIP_FAILED',
          message: 'Failed to create zip bundle.',
          detail: {
            error: error instanceof Error ? error.message : String(error),
          },
        },
      };
      (self as DedicatedWorkerGlobalScope).postMessage(response);
      return;
    }

    const bundleBytes = toTransferBuffer(zipBytes);
    const done: WorkerDone = {
      type: 'DONE',
      id: message.id,
      bundleName: `${base}.zip`,
      bundleBytes,
      meshStats,
      conversionWarnings,
    };
    (self as DedicatedWorkerGlobalScope).postMessage(done, [bundleBytes]);
  } catch (error) {
    const asAny = error as any;
    const forcedCode =
      typeof asAny?.__code === 'string'
        ? (asAny.__code as StepConverterErrorCode)
        : null;
    const forcedDetail =
      asAny?.detail && typeof asAny.detail === 'object'
        ? (asAny.detail as Record<string, unknown>)
        : undefined;
    const err = forcedCode
      ? ({
          code: forcedCode,
          message: asAny?.message ?? 'Conversion failed.',
          ...(forcedDetail ? { detail: forcedDetail } : {}),
        } satisfies StepConverterError)
      : normalizeWorkerError(error);
    const response: WorkerError = {
      type: 'ERROR',
      id: message.id,
      error: err,
    };
    (self as DedicatedWorkerGlobalScope).postMessage(response);
  }
}

self.onmessage = async (
  event: MessageEvent<WorkerStartRequest | WorkerRequest>
) => {
  if (event.data && typeof event.data === 'object' && 'type' in event.data) {
    if (event.data.type === 'START') {
      await handleStartMessage(event.data);
      return;
    }
  }

  // Legacy API (kept for compatibility; browser converter UI is migrated in Task 3).
  const {
    id,
    input,
    inputFormat,
    outputFormat,
    triangulate,
    includeBom,
    includeNodeMap,
  } = event.data as WorkerRequest;
  try {
    const converter = await converterPromise;
    const docHandle = converter.readBuffer(new Uint8Array(input), inputFormat, {
      preserveNames: true,
      preserveColors: true,
      preserveLayers: true,
      preserveMaterials: true,
    });
    converter.triangulate(docHandle.get(), triangulate);
    const result = converter.writeBuffer(docHandle, outputFormat, {
      nameFormat: 'productOrInstance',
    });
    let bom: unknown;
    let nodeMap: unknown;
    if (includeBom || includeNodeMap) {
      const metadata = converter.createMetadataFromGlb(docHandle);
      if (includeBom) {
        bom = metadata.bom;
      }
      if (includeNodeMap) {
        nodeMap = metadata.nodeMap;
      }
    }
    const [response, transfer] = mapResult(result, bom, nodeMap);
    response.id = id;
    (self as DedicatedWorkerGlobalScope).postMessage(response, transfer);
  } catch (error) {
    const response: WorkerFailure = {
      id,
      ok: false,
      error: error instanceof Error ? error.message : 'Conversion failed.',
    };
    (self as DedicatedWorkerGlobalScope).postMessage(response);
  }
};
