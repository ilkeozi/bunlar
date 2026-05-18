import {
  ConversionError,
  ValidationError,
  convertCadBufferToGlbWithMetadata,
  createConverter,
  maxDimension,
  type GlbGeometryStats,
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

type MeshStats = GlbGeometryStats;

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
    postProgress('meshing');
    postProgress('writing');
    const triangulateOriginal = message.triangulate ?? {};
    const { glb, patchedGlb, meshStats, conversionWarnings, metadata } =
      convertCadBufferToGlbWithMetadata(converter, new Uint8Array(message.fileBytes), {
        inputFormat,
        triangulate: triangulateOriginal,
        nameFormat: 'productAndInstanceAndOcaf',
        readOptions: {
          preserveNames: true,
          preserveColors: true,
          preserveLayers: true,
          preserveMaterials: true,
        },
        schemaVersion: 'bunlar-step-converter@1',
        embedMetadataKey: 'bunlarStepConverter',
        validateNodeMap: true,
        validateMesh: true,
      });

    const base = baseNameFromFilename(message.filename);

    postProgress('metadata');

    const { boundsMeters, units } = metadata;
    const scaleToMeters = units.scaleToMeters;
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

    postProgress('packaging');
    let zipBytes: Uint8Array;
    try {
      const glbToZip = patchedGlb ?? glb;
      zipBytes = zipSync(
        {
          [`${base}.glb`]: glbToZip,
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
