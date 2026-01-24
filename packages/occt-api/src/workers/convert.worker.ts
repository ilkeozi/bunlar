import { parentPort } from "node:worker_threads";
import type { ConvertOptions, InputFormat } from "opencascade-convert";
import { createConverter } from "opencascade-convert";

type MetadataPayload = {
  inputPath: string;
  inputFormat: InputFormat;
  includeBom?: boolean;
  includeNodeMap?: boolean;
};

type WorkerRequest =
  | { id: number; type: "convert"; payload: ConvertOptions }
  | { id: number; type: "metadata"; payload: MetadataPayload };

type WorkerResponse =
  | { id: number; ok: true; result: unknown }
  | { id: number; ok: false; error: string };

if (!parentPort) {
  throw new Error("convert worker must be run inside a worker thread");
}

const converterPromise = createConverter();

parentPort.on("message", async (message: WorkerRequest) => {
  try {
    const converter = await converterPromise;
    if (message.type === "convert") {
      const result = converter.convert(message.payload);
      const response: WorkerResponse = { id: message.id, ok: true, result };
      parentPort.postMessage(response);
      return;
    }
    const includeBom = message.payload.includeBom ?? true;
    const includeNodeMap = message.payload.includeNodeMap ?? true;
    const docHandle = converter.read(
      message.payload.inputPath,
      message.payload.inputFormat,
      {
        preserveNames: true,
        preserveColors: true,
        preserveLayers: true,
        preserveMaterials: true,
      }
    );
    const metadata = converter.createMetadataFromGlb(docHandle);
    const response: WorkerResponse = {
      id: message.id,
      ok: true,
      result: {
        bom: includeBom ? metadata.bom : undefined,
        nodeMap: includeNodeMap ? metadata.nodeMap : undefined,
      },
    };
    parentPort.postMessage(response);
  } catch (error) {
    const response: WorkerResponse = {
      id: message.id,
      ok: false,
      error: error instanceof Error ? error.message : "Worker request failed.",
    };
    parentPort.postMessage(response);
  }
});
