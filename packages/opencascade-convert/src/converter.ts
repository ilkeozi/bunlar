import fs from 'node:fs';
import path from 'node:path';
import type {
  ConvertBufferFileOptions,
  ConvertBufferOptions,
  ConvertBufferResult,
  ConvertFileOptions,
  ConvertOptions,
  ConvertResult,
  InputFormat,
  OutputFormat,
  ReadOptions,
  TriangulateOptions,
  WriteOptions,
} from './core/types';
import { resolveInputFormat, resolveOutputFormat } from './core/formats';
import { ValidationError } from './core/errors';
import { readCadBuffer, readCadFile, type OcctDocumentHandle } from './occt/document';
import { triangulateDocument } from './occt/triangulation';
import { writeDocument, writeDocumentToBuffer } from './occt/writer';
import { buildBom, buildNodeMap } from './occt/assembly';
import { extractNameOverridesFromGlb } from './occt/gltf-names';
import type { OpenCascadeInstance } from './occt/loader';
import { getOpenCascade, loadOpenCascade } from './occt/loader';
import type { NameFormat } from './core/types';

export class OpenCascadeConverter {
  constructor(private readonly oc: OpenCascadeInstance) {}

  read(inputPath: string, format: InputFormat, options?: ReadOptions): OcctDocumentHandle {
    return readCadFile(this.oc, inputPath, format, options);
  }

  triangulate(doc: any, options?: TriangulateOptions) {
    triangulateDocument(this.oc, doc, options);
  }

  write(docHandle: OcctDocumentHandle, outputPath: string, format: OutputFormat, options?: WriteOptions) {
    writeDocument(this.oc, docHandle, outputPath, format, options);
  }

  createNodeMap(docHandle: OcctDocumentHandle) {
    return buildNodeMap(this.oc, docHandle);
  }

  createBom(docHandle: OcctDocumentHandle) {
    return buildBom(this.oc, docHandle);
  }

  createMetadataFromGlb(
    docHandle: OcctDocumentHandle,
    options?: { nameFormat?: NameFormat }
  ) {
    const glbResult = writeDocumentToBuffer(this.oc, docHandle, 'glb', {
      nameFormat: options?.nameFormat ?? 'productAndInstanceAndOcaf',
    });
    if (glbResult.outputFormat !== 'glb') {
      throw new Error('Expected GLB buffer when extracting metadata.');
    }
    const overrides = extractNameOverridesFromGlb(glbResult.glb);
    return {
      nodeMap: buildNodeMap(this.oc, docHandle, overrides),
      bom: buildBom(this.oc, docHandle, overrides),
    };
  }

  convertBuffer(options: ConvertBufferOptions): ConvertBufferResult {
    if (!options.inputFormat) {
      throw new ValidationError('inputFormat is required for buffer conversion.');
    }
    if (!options.outputFormat) {
      throw new ValidationError('outputFormat is required for buffer conversion.');
    }

    const docHandle = readCadBuffer(this.oc, options.input, options.inputFormat, options.read);
    this.triangulate(docHandle.get(), options.triangulate);
    return writeDocumentToBuffer(this.oc, docHandle, options.outputFormat, options.write);
  }

  convert(options: ConvertOptions): ConvertResult {
    const inputPath = path.resolve(options.inputPath);
    const outputPath = path.resolve(options.outputPath);

    if (!fs.existsSync(inputPath)) {
      throw new ValidationError(`Input file not found: ${inputPath}`);
    }

    const inputFormat = resolveInputFormat(inputPath);
    if (!inputFormat) {
      throw new ValidationError('Input must be STEP or IGES (.step, .stp, .igs, .iges).');
    }

    const outputFormat = resolveOutputFormat(outputPath, options.format);
    if (!outputFormat) {
      throw new ValidationError('Output must be .obj, .gltf, or .glb (or specify format).');
    }

    const docHandle = this.read(inputPath, inputFormat, options.read);
    this.triangulate(docHandle.get(), options.triangulate);
    this.write(docHandle, outputPath, outputFormat, options.write);

    return { inputPath, outputPath, format: outputFormat };
  }
}

export async function createConverter(options?: { cwd?: string; cache?: boolean }) {
  const oc = await getOpenCascade(options);
  return new OpenCascadeConverter(oc);
}

export async function convertFile(options: ConvertFileOptions) {
  const converter = await createConverter(options.loader);
  return converter.convert(options);
}

export async function convertBuffer(options: ConvertBufferFileOptions) {
  const converter = await createConverter(options.loader);
  return converter.convertBuffer(options);
}

export async function createIsolatedConverter(options?: { cwd?: string }) {
  const oc = await loadOpenCascade({ cwd: options?.cwd, cache: false });
  return new OpenCascadeConverter(oc);
}
