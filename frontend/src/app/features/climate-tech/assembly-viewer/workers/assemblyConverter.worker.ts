/// <reference lib="webworker" />
import {
  createConverter,
  type ConvertBufferResult,
  type InputFormat,
} from 'opencascade-convert/browser';
import type { BomExport, NodeMap } from 'opencascade-convert/browser';

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
  triangulate: TriangulatePayload;
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
  bom: BomExport;
  nodeMap: NodeMap;
};

type WorkerFailure = {
  id: number;
  ok: false;
  error: string;
};

const converterPromise = createConverter();

function toTransferBuffer(data: Uint8Array): ArrayBuffer {
  const copy = new Uint8Array(data);
  return copy.buffer;
}

function mapResult(
  result: ConvertBufferResult
): [WorkerModelSuccess, ArrayBuffer[]] {
  if (result.outputFormat === 'glb') {
    const data = toTransferBuffer(result.glb);
    return [{ id: 0, ok: true, phase: 'model', data }, [data]];
  }
  throw new Error('Unexpected output format.');
}

self.onmessage = async (event: MessageEvent<WorkerRequest>) => {
  const { id, input, inputFormat, triangulate } = event.data;
  try {
    const converter = await converterPromise;
    const docHandle = converter.readBuffer(new Uint8Array(input), inputFormat, {
      preserveNames: true,
      preserveColors: true,
      preserveLayers: true,
      preserveMaterials: true,
    });
    converter.triangulate(docHandle.get(), triangulate);
    const result = converter.writeBuffer(docHandle, 'glb', {
      nameFormat: 'productAndInstanceAndOcaf',
    });
    const [modelResponse, transfer] = mapResult(result);
    modelResponse.id = id;
    self.postMessage(modelResponse, transfer);

    const metadata = converter.createMetadataFromGlb(docHandle, {
      nameFormat: 'productAndInstanceAndOcaf',
    });
    const metadataResponse: WorkerMetadataSuccess = {
      id,
      ok: true,
      phase: 'metadata',
      bom: metadata.bom,
      nodeMap: metadata.nodeMap,
    };
    self.postMessage(metadataResponse);
  } catch (error) {
    const response: WorkerFailure = {
      id,
      ok: false,
      error: error instanceof Error ? error.message : 'Conversion failed.',
    };
    self.postMessage(response);
  }
};
