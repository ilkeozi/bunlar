import {
  ConversionError,
  ValidationError,
  createConverter,
  type ConvertBufferResult,
  type InputFormat,
  type OutputFormat,
} from 'opencascade-convert/browser';

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
  glbBytes: ArrayBuffer;
  baseName?: string;
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
    return { code: 'CONVERSION_FAILED', message: error.message };
  }

  if (error instanceof ConversionError) {
    if (/could not read/i.test(error.message)) {
      return { code: 'INVALID_STEP', message: 'Invalid or corrupt STEP file.' };
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
  return { code: 'CONVERSION_FAILED', message };
}

async function convertStepToGlb(params: {
  fileBytes: ArrayBuffer;
  inputFormat: InputFormat;
  triangulate: TriangulatePayload;
  nameFormat?: 'productOrInstance' | 'productAndInstanceAndOcaf';
}) {
  const converter = await converterPromise;
  const docHandle = converter.readBuffer(
    new Uint8Array(params.fileBytes),
    params.inputFormat,
    {
      preserveNames: true,
      preserveColors: true,
      preserveLayers: true,
      preserveMaterials: true,
    }
  );
  converter.triangulate(docHandle.get(), params.triangulate);
  const result = converter.writeBuffer(docHandle, 'glb', {
    nameFormat: params.nameFormat ?? 'productOrInstance',
  });
  if (result.outputFormat !== 'glb') {
    throw new Error('Expected GLB output.');
  }
  return result.glb;
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
    postProgress('parsing');
    const inputFormat: InputFormat = 'step';
    postProgress('meshing');
    const glb = await convertStepToGlb({
      fileBytes: message.fileBytes,
      inputFormat,
      triangulate: message.triangulate,
    });
    postProgress('writing');

    const glbBytes = toTransferBuffer(glb);
    const done: WorkerDone = {
      type: 'DONE',
      id: message.id,
      glbBytes,
      baseName: baseNameFromFilename(message.filename),
    };
    (self as DedicatedWorkerGlobalScope).postMessage(done, [glbBytes]);
  } catch (error) {
    const err = normalizeWorkerError(error);
    const response: WorkerError = { type: 'ERROR', id: message.id, error: err };
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
