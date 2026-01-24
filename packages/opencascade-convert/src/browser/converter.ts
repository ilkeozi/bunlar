import type {
  ConvertBufferFileOptions,
  ConvertBufferOptions,
  ConvertBufferResult,
  InputFormat,
  LoaderOptions,
  NameFormat,
  ReadOptions,
  TriangulateOptions,
  WriteOptions,
} from '../core/types';
import { ValidationError } from '../core/errors';
import { readCadBuffer, type OcctDocumentHandle } from '../occt/document';
import { triangulateDocument } from '../occt/triangulation';
import { writeDocumentToBuffer } from '../occt/writer';
import { buildBom, buildNodeMap } from '../occt/assembly';
import { extractNameOverridesFromGlb } from '../occt/gltf-names';
import type { OpenCascadeInstance } from '../occt/types';
import { getOpenCascade, loadOpenCascade } from '../occt/loader-browser';

export class OpenCascadeConverter {
  constructor(private readonly oc: OpenCascadeInstance) {}

  readBuffer(input: Uint8Array, format: InputFormat, options?: ReadOptions): OcctDocumentHandle {
    return readCadBuffer(this.oc, input, format, options);
  }

  read(input: Uint8Array, format: InputFormat, options?: ReadOptions): OcctDocumentHandle {
    return this.readBuffer(input, format, options);
  }

  triangulate(doc: any, options?: TriangulateOptions) {
    triangulateDocument(this.oc, doc, options);
  }

  writeBuffer(docHandle: OcctDocumentHandle, format: ConvertBufferOptions['outputFormat'], options?: WriteOptions) {
    return writeDocumentToBuffer(this.oc, docHandle, format, options);
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
}

export async function createConverter(options?: LoaderOptions) {
  const oc = await getOpenCascade(options);
  return new OpenCascadeConverter(oc);
}

export async function convertBuffer(options: ConvertBufferFileOptions) {
  const converter = await createConverter(options.loader);
  return converter.convertBuffer(options);
}

export async function createIsolatedConverter() {
  const oc = await loadOpenCascade({ cache: false });
  return new OpenCascadeConverter(oc);
}

export async function convertFile(): Promise<never> {
  throw new ValidationError('convertFile is only supported in Node.js. Use convertBuffer in the browser.');
}
