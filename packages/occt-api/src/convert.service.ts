import { Injectable } from "@nestjs/common";
import fs from "node:fs";
import path from "node:path";
import { createConverter } from "opencascade-convert";

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

let converterPromise: ReturnType<typeof createConverter> | null = null;

@Injectable()
export class ConvertService {
  async convert(request: ConvertRequest) {
    const inputPath = path.resolve(request.inputPath || "");
    const outputPath = path.resolve(request.outputPath || "");

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
      const converter = await getConverter();
      converter.convert({
        inputPath,
        outputPath,
        format,
        read: {
          preserveNames: true,
          preserveColors: true,
          preserveLayers: true,
          preserveMaterials: true,
        },
        triangulate: {
          linearDeflection: request.linDeflection,
          angularDeflection: request.angDeflection,
          relative: request.relative,
          parallel: request.parallel,
        },
        write: {
          nameFormat: "productOrInstance"
        }
      });

      return { ok: true, outputPath };
    } catch (error) {
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
      const converter = await getConverter();
      const docHandle = converter.read(inputPath, inputFormat, {
        preserveNames: true,
        preserveColors: true,
        preserveLayers: true,
        preserveMaterials: true
      });

      const includeBom = request.includeBom ?? true;
      const includeNodeMap = request.includeNodeMap ?? true;
      const metadata = converter.createMetadataFromGlb(docHandle);

      return {
        ok: true,
        bom: includeBom ? metadata.bom : undefined,
        nodeMap: includeNodeMap ? metadata.nodeMap : undefined
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

function resolveInputFormat(inputPath: string) {
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

function getConverter() {
  if (!converterPromise) {
    converterPromise = createConverter();
  }
  return converterPromise;
}
