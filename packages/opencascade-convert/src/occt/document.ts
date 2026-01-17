import fs from 'node:fs';
import path from 'node:path';
import type { InputFormat, ReadOptions } from '../core/types';
import { ConversionError } from '../core/errors';
import type { OpenCascadeInstance } from './loader';

export type OcctDocumentHandle = any;

const DEFAULT_READ_OPTIONS: Required<ReadOptions> = {
  preserveNames: true,
  preserveColors: true,
  preserveLayers: true,
  preserveMaterials: true,
};

export function readCadFile(
  oc: OpenCascadeInstance,
  inputPath: string,
  format: InputFormat,
  options: ReadOptions = {}
): OcctDocumentHandle {
  const payload = fs.readFileSync(inputPath);
  return readCadBuffer(oc, payload, format, options);
}

export function readCadBuffer(
  oc: OpenCascadeInstance,
  payload: Uint8Array,
  format: InputFormat,
  options: ReadOptions = {}
): OcctDocumentHandle {
  const fileName = format === 'step' ? 'file.stp' : 'file.igs';
  const reader =
    format === 'step' ? new oc.STEPCAFControl_Reader_1() : new oc.IGESCAFControl_Reader_1();
  applyReaderSettings(reader, { ...DEFAULT_READ_OPTIONS, ...options });
  return transferDocument(oc, reader, payload, fileName);
}

function applyReaderSettings(reader: any, options: ReadOptions) {
  if (options.preserveNames && typeof reader.SetNameMode === 'function') {
    reader.SetNameMode(true);
  }
  if (options.preserveColors && typeof reader.SetColorMode === 'function') {
    reader.SetColorMode(true);
  }
  if (options.preserveLayers && typeof reader.SetLayerMode === 'function') {
    reader.SetLayerMode(true);
  }
  if (options.preserveMaterials && typeof reader.SetMatMode === 'function') {
    reader.SetMatMode(true);
  }
}

function transferDocument(
  oc: OpenCascadeInstance,
  reader: any,
  data: Uint8Array,
  fileName: string
): OcctDocumentHandle {
  const base = '.';
  const filePath = path.posix.join(base, fileName);
  oc.FS.createDataFile(base, fileName, data, true, true, true);

  const result = reader.ReadFile(filePath);
  oc.FS.unlink(filePath);

  if (result !== oc.IFSelect_ReturnStatus.IFSelect_RetDone) {
    throw new ConversionError(`Could not read ${fileName} file`);
  }

  const format = new oc.TCollection_ExtendedString_1();
  const doc = new oc.TDocStd_Document(format);
  const docHandle = new oc.Handle_TDocStd_Document_2(doc);
  const progress = new oc.Message_ProgressRange_1();
  reader.Transfer_1 ? reader.Transfer_1(docHandle, progress) : reader.Transfer(docHandle, progress);
  return docHandle;
}
