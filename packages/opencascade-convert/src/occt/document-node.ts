import fs from 'node:fs';
import type { InputFormat, ReadOptions } from '../core/types';
import type { OpenCascadeInstance } from './types';
import { readCadBuffer, type OcctDocumentHandle } from './document';

export function readCadFile(
  oc: OpenCascadeInstance,
  inputPath: string,
  format: InputFormat,
  options: ReadOptions = {}
): OcctDocumentHandle {
  const payload = fs.readFileSync(inputPath);
  return readCadBuffer(oc, payload, format, options);
}
