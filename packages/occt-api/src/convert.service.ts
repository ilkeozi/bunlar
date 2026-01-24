import { Injectable } from "@nestjs/common";
import fs from "node:fs";
import path from "node:path";
import { Worker } from "node:worker_threads";
import type { ConvertOptions, ConvertResult, InputFormat } from "opencascade-convert";

export type ConvertFormat = "obj" | "gltf" | "glb";

export type ConvertRequest = {
  inputPath: string;
  outputPath: string;
  format?: ConvertFormat;
  linDeflection?: number;
  angDeflection?: number;
  relative?: boolean;
  parallel?: boolean;
};

export type MetadataRequest = {
  inputPath: string;
  includeBom?: boolean;
  includeNodeMap?: boolean;
};

const SUPPORTED_INPUTS = new Set([".igs", ".iges", ".step", ".stp"]);
const DEFAULT_TRIANGULATION = {
  linearDeflection: 1,
  angularDeflection: 0.5,
  relative: false,
  parallel: true,
};

type ConvertWorkerPayload = ConvertOptions;

type MetadataWorkerPayload = {
  inputPath: string;
  inputFormat: InputFormat;
  includeBom?: boolean;
  includeNodeMap?: boolean;
};

type WorkerRequest =
  | { id: number; type: "convert"; payload: ConvertWorkerPayload }
  | { id: number; type: "metadata"; payload: MetadataWorkerPayload };

type WorkerResponse =
  | { id: number; ok: true; result: unknown }
  | { id: number; ok: false; error: string };

type WorkerTask<T> = {
  id: number;
  type: WorkerRequest["type"];
  payload: ConvertWorkerPayload | MetadataWorkerPayload;
  resolve: (value: T) => void;
  reject: (error: Error) => void;
};

class ConverterWorker {
  private worker: Worker;
  private busy = false;
  private nextId = 1;
  private readonly queue: Array<WorkerTask<unknown>> = [];
  private readonly pending = new Map<number, WorkerTask<unknown>>();

  constructor() {
    this.worker = this.createWorker();
    this.worker.on("message", this.handleMessage);
    this.worker.on("error", this.handleError);
    this.worker.on("exit", this.handleExit);
  }

  async convert(payload: ConvertWorkerPayload) {
    return this.enqueue<ConvertResult>("convert", payload);
  }

  async metadata(payload: MetadataWorkerPayload) {
    return this.enqueue<{
      bom?: unknown;
      nodeMap?: unknown;
    }>("metadata", payload);
  }

  private enqueue<T>(
    type: WorkerRequest["type"],
    payload: ConvertWorkerPayload | MetadataWorkerPayload
  ) {
    return new Promise<T>((resolve, reject) => {
      const id = this.nextId++;
      this.queue.push({
        id,
        type,
        payload,
        resolve: resolve as (value: unknown) => void,
        reject,
      });
      this.dispatch();
    });
  }

  private dispatch() {
    if (this.busy) return;
    const next = this.queue.shift();
    if (!next) return;
    this.busy = true;
    this.pending.set(next.id, next);
    const request: WorkerRequest = {
      id: next.id,
      type: next.type,
      payload: next.payload,
    };
    this.worker.postMessage(request);
  }

  private handleMessage = (message: WorkerResponse) => {
    const task = this.pending.get(message.id);
    if (!task) return;
    this.pending.delete(message.id);
    this.busy = false;
    if (message.ok) {
      task.resolve(message.result);
    } else {
      task.reject(new Error(message.error));
    }
    this.dispatch();
  };

  private handleError = (error: Error) => {
    this.failAll(error);
    this.restartWorker();
  };

  private handleExit = (code: number) => {
    this.failAll(new Error(`converter worker exited with code ${code}`));
    this.restartWorker();
  };

  private failAll(error: Error) {
    for (const task of this.pending.values()) {
      task.reject(error);
    }
    this.pending.clear();
    while (this.queue.length > 0) {
      const task = this.queue.shift();
      if (task) {
        task.reject(error);
      }
    }
    this.busy = false;
  }

  private restartWorker() {
    this.worker.removeAllListeners();
    this.worker = this.createWorker();
    this.worker.on("message", this.handleMessage);
    this.worker.on("error", this.handleError);
    this.worker.on("exit", this.handleExit);
  }

  private createWorker() {
    const workerPath = resolveWorkerPath();
    const execArgv = workerPath.endsWith(".ts")
      ? ["-r", "@swc-node/register"]
      : [];
    return new Worker(workerPath, { execArgv });
  }
}

const converterWorker = new ConverterWorker();

@Injectable()
export class ConvertService {
  async convert(request: ConvertRequest) {
    const inputPath = path.resolve(request.inputPath || "");
    const outputPath = path.resolve(request.outputPath || "");
    const startedAt = Date.now();

    if (!request.inputPath || !request.outputPath) {
      return { ok: false, error: "inputPath and outputPath are required." };
    }
    if (!fs.existsSync(inputPath)) {
      return { ok: false, error: `Input file not found: ${inputPath}` };
    }

    const format = resolveFormat(request.format, outputPath);
    if (!format) {
      return { ok: false, error: "Missing or unsupported output format." };
    }

    const inputExt = path.extname(inputPath).toLowerCase();
    if (!SUPPORTED_INPUTS.has(inputExt)) {
      return { ok: false, error: "Input must be STEP or IGES (.step, .stp, .igs, .iges)." };
    }

    try {
      const triangulate = {
        linearDeflection:
          request.linDeflection ?? DEFAULT_TRIANGULATION.linearDeflection,
        angularDeflection:
          request.angDeflection ?? DEFAULT_TRIANGULATION.angularDeflection,
        relative: request.relative ?? DEFAULT_TRIANGULATION.relative,
        parallel: request.parallel ?? DEFAULT_TRIANGULATION.parallel,
      };
      const result = await converterWorker.convert({
        inputPath,
        outputPath,
        format,
        read: {
          preserveNames: true,
          preserveColors: true,
          preserveLayers: true,
          preserveMaterials: true,
        },
        triangulate,
        write: {
          nameFormat: "productOrInstance"
        }
      });

      return { ok: true, outputPath: result.outputPath };
    } catch (error) {
      console.error("[occt-api] convert failed", {
        ms: Date.now() - startedAt,
        error: error instanceof Error ? error.message : error,
      });
      return {
        ok: false,
        error: error instanceof Error ? error.message : "Conversion failed.",
      };
    }
  }

  async extractMetadata(request: MetadataRequest) {
    const inputPath = path.resolve(request.inputPath || "");

    if (!request.inputPath) {
      return { ok: false, error: "inputPath is required." };
    }
    if (!fs.existsSync(inputPath)) {
      return { ok: false, error: `Input file not found: ${inputPath}` };
    }

    const inputFormat = resolveInputFormat(inputPath);
    if (!inputFormat) {
      return { ok: false, error: "Input must be STEP or IGES (.step, .stp, .igs, .iges)." };
    }

    try {
      const metadata = await converterWorker.metadata({
        inputPath,
        inputFormat,
        includeBom: request.includeBom,
        includeNodeMap: request.includeNodeMap,
      });

      return {
        ok: true,
        bom: metadata.bom,
        nodeMap: metadata.nodeMap
      };
    } catch (error) {
      return {
        ok: false,
        error: error instanceof Error ? error.message : "Metadata extraction failed."
      };
    }
  }
}

function resolveFormat(format: ConvertFormat | undefined, outputPath: string) {
  if (format) {
    return format;
  }
  const ext = path.extname(outputPath).toLowerCase();
  if (ext === ".obj") return "obj";
  if (ext === ".gltf") return "gltf";
  if (ext === ".glb") return "glb";
  return null;
}

function resolveInputFormat(inputPath: string): InputFormat | null {
  const ext = path.extname(inputPath).toLowerCase();
  if (ext === ".obj" || ext === ".gltf" || ext === ".glb") {
    return null;
  }
  if (ext === ".igs" || ext === ".iges") {
    return "iges";
  }
  if (ext === ".step" || ext === ".stp") {
    return "step";
  }
  return null;
}

function resolveWorkerPath() {
  const jsPath = path.join(__dirname, "workers", "convert.worker.js");
  if (fs.existsSync(jsPath)) {
    return jsPath;
  }
  return path.join(__dirname, "workers", "convert.worker.ts");
}
