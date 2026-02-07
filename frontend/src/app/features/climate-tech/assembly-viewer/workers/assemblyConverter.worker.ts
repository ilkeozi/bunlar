import { createConverter, type InputFormat } from 'opencascade-convert/browser';

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

    converter.triangulate(docHandle.get(), triangulate);
    const result = converter.writeBuffer(docHandle, 'glb', {
      nameFormat: 'productAndInstanceAndOcaf',
    });

    if (result.outputFormat !== 'glb') {
      throw new Error('Failed to generate GLB output.');
    }

    const model = toTransferBuffer(result.glb);
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
