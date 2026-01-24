import fs from 'node:fs';
import path from 'node:path';
import type { OutputFormat, WriteOptions } from '../core/types';
import type { OpenCascadeInstance } from './types';
import type { OcctDocumentHandle } from './document';
import { writeGlbInternal, writeGltfInternal, writeObjInternal } from './writer-core';

export function writeDocument(
  oc: OpenCascadeInstance,
  docHandle: OcctDocumentHandle,
  outputPath: string,
  format: OutputFormat,
  options: WriteOptions = {}
) {
  const internalPath = `./${path.basename(outputPath)}`;
  if (format === 'glb') {
    const data = writeGlbInternal(oc, docHandle, internalPath, options);
    if (data) {
      fs.writeFileSync(outputPath, data);
    }
    return;
  }

  if (format === 'gltf') {
    const { gltfData, binData, binPath } = writeGltfInternal(oc, docHandle, internalPath, options);
    if (gltfData) {
      fs.writeFileSync(outputPath, gltfData);
    }
    if (binData) {
      const externalBinPath = path.join(path.dirname(outputPath), path.basename(binPath));
      fs.writeFileSync(externalBinPath, binData);
    }
    return;
  }

  const data = writeObjInternal(oc, docHandle, internalPath, options);
  if (data) {
    fs.writeFileSync(outputPath, data);
  }
}
