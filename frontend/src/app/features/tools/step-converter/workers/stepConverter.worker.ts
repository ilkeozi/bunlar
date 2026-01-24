import {
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
  return data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength);
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

self.onmessage = async (event: MessageEvent<WorkerRequest>) => {
  const { id, input, inputFormat, outputFormat, triangulate, includeBom, includeNodeMap } =
    event.data;
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
