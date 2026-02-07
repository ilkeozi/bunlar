import { createConverter, type InputFormat } from 'opencascade-convert/browser';

type ConversionWarning = {
  code: string;
  message: string;
  detail?: Record<string, unknown>;
};

type MeshStats = {
  triangles: number;
  primitiveCount: number;
  meshCount: number;
  nodeCount: number;
  nodesWithMeshCount: number;
};

const TRIANGLE_EXPLOSION_THRESHOLDS = {
  MAX_TRIANGLES: 5_000_000,
  MAX_PRIMITIVES: 50_000,
} as const;

function isTriangleExplosion(meshStats: MeshStats) {
  return (
    meshStats.triangles > TRIANGLE_EXPLOSION_THRESHOLDS.MAX_TRIANGLES ||
    meshStats.primitiveCount > TRIANGLE_EXPLOSION_THRESHOLDS.MAX_PRIMITIVES
  );
}

type WorkerRequest = {
  id: number;
  input: ArrayBuffer;
  inputFormat: InputFormat;
  triangulate: {
    linearDeflection?: number;
    angularDeflection?: number;
    relative?: boolean;
    parallel?: boolean;
  };
};

type WorkerModelSuccess = {
  id: number;
  ok: true;
  phase: 'model';
  data: ArrayBuffer;
};

type WorkerMetadataSuccess = {
  id: number;
  ok: true;
  phase: 'metadata';
  bom: unknown;
  nodeMap: unknown;
  meshStats: MeshStats;
  conversionWarnings: ConversionWarning[];
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

function summarizeGlbGeometry(glb: Uint8Array): MeshStats {
  const gltf = parseGlbJson(glb) as any;
  const accessors = Array.isArray(gltf?.accessors)
    ? (gltf.accessors as any[])
    : [];
  const meshes = Array.isArray(gltf?.meshes) ? (gltf.meshes as any[]) : [];
  const nodes = Array.isArray(gltf?.nodes) ? (gltf.nodes as any[]) : [];

  let triangles = 0;
  let primitiveCount = 0;
  meshes.forEach((mesh) => {
    (mesh?.primitives ?? []).forEach((prim: any) => {
      primitiveCount += 1;

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

      const posAccessorIndex = prim?.attributes?.POSITION;
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

  return {
    triangles,
    primitiveCount,
    meshCount: meshes.length,
    nodeCount: nodes.length,
    nodesWithMeshCount,
  };
}

self.onmessage = async (event: MessageEvent<WorkerRequest>) => {
  const { id, input, inputFormat, triangulate } = event.data;
  const ctx = self as any;
  try {
    const converter = await converterPromise;
    const docHandle = converter.readBuffer(new Uint8Array(input), inputFormat, {
      preserveNames: true,
      preserveColors: true,
      preserveLayers: true,
      preserveMaterials: true,
    });

    const conversionWarnings: ConversionWarning[] = [];
    const triangulateOriginal = triangulate ?? {};

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

    const linearDeflection0 = triangulateOriginal.linearDeflection ?? 1;
    const angularDeflection0 = triangulateOriginal.angularDeflection ?? 0.5;

    const triangulateForAttempt = (attempt: number) => {
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

    for (let attempt = 0; attempt < 3; attempt += 1) {
      const triangulateUsed = triangulateForAttempt(attempt);
      converter.triangulate(docHandle.get(), triangulateUsed);
      const result = converter.writeBuffer(docHandle, 'glb', {
        nameFormat: 'productAndInstanceAndOcaf',
      });

      if (result.outputFormat !== 'glb') {
        throw new Error('Failed to generate GLB output.');
      }

      glb = result.glb;
      const stats = summarizeGlbGeometry(glb);
      meshStats = stats;

      if (!isTriangleExplosion(stats)) {
        break;
      }

      const detail = {
        attempt,
        thresholds: TRIANGLE_EXPLOSION_THRESHOLDS,
        meshStats: stats,
        triangulateUsed,
      };

      if (attempt < 2) {
        conversionWarnings.push({
          code: 'mesh/triangle-explosion-retry',
          message: `Triangle explosion detected on attempt ${attempt}; meshing was coarsened and retried.`,
          detail,
        });
        continue;
      }

      conversionWarnings.push({
        code: 'mesh/triangle-explosion-unresolved',
        message:
          'Triangle explosion thresholds were exceeded after the final attempt.',
        detail,
      });
      break;
    }

    if (!glb || !meshStats) {
      throw new Error('Failed to generate GLB output.');
    }

    const model = toTransferBuffer(glb);
    const modelMsg: WorkerModelSuccess = {
      id,
      ok: true,
      phase: 'model',
      data: model,
    };
    ctx.postMessage(modelMsg, [model]);

    let bom: unknown;
    let nodeMap: unknown;
    if (typeof (converter as any).createMetadataFromGlb === 'function') {
      const metadata = (converter as any).createMetadataFromGlb(docHandle);
      bom = metadata?.bom;
      nodeMap = metadata?.nodeMap;
    } else {
      bom = (converter as any).createBom(docHandle);
      nodeMap = (converter as any).createNodeMap(docHandle);
    }

    const metadataMsg: WorkerMetadataSuccess = {
      id,
      ok: true,
      phase: 'metadata',
      bom,
      nodeMap,
      meshStats,
      conversionWarnings,
    };
    ctx.postMessage(metadataMsg);
  } catch (error) {
    const errMsg: WorkerFailure = {
      id,
      ok: false,
      error: error instanceof Error ? error.message : 'Conversion failed.',
    };
    ctx.postMessage(errMsg);
  }
};
