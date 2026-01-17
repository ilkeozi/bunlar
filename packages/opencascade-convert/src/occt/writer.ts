import fs from 'node:fs';
import path from 'node:path';
import type { ConvertBufferResult, OutputFormat, WriteOptions } from '../core/types';
import { ConversionError } from '../core/errors';
import { resolveNameFormatKey } from '../core/name-format';
import type { OpenCascadeInstance } from './loader';
import type { OcctDocumentHandle } from './document';

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

export function writeDocumentToBuffer(
  oc: OpenCascadeInstance,
  docHandle: OcctDocumentHandle,
  format: OutputFormat,
  options: WriteOptions = {}
): ConvertBufferResult {
  if (format === 'glb') {
    const data = writeGlbInternal(oc, docHandle, './output.glb', options);
    if (!data) {
      throw new ConversionError('Failed to generate GLB output.');
    }
    return { outputFormat: 'glb', glb: Buffer.from(data) };
  }

  if (format === 'gltf') {
    const { gltfData, binData } = writeGltfInternal(oc, docHandle, './output.gltf', options);
    if (!gltfData || !binData) {
      throw new ConversionError('Failed to generate GLTF output.');
    }
    return { outputFormat: 'gltf', gltf: Buffer.from(gltfData), bin: Buffer.from(binData) };
  }

  const data = writeObjInternal(oc, docHandle, './output.obj', options);
  if (!data) {
    throw new ConversionError('Failed to generate OBJ output.');
  }
  return { outputFormat: 'obj', obj: Buffer.from(data) };
}

function createMetadataMap(oc: OpenCascadeInstance, metadata?: Record<string, string>) {
  const map = new oc.TColStd_IndexedDataMapOfStringString_1();
  if (!metadata) {
    return map;
  }
  Object.entries(metadata).forEach(([key, value]) => {
    const k = new oc.TCollection_AsciiString_2(key);
    const v = new oc.TCollection_AsciiString_2(value);
    map.Add(k, v);
  });
  return map;
}

function applyGltfNameFormat(oc: OpenCascadeInstance, writer: any, options: WriteOptions) {
  if (!writer || typeof writer.SetNodeNameFormat !== 'function') {
    return;
  }
  const formatKey = resolveNameFormatKey(options.nameFormat);
  const format = oc.RWMesh_NameFormat[formatKey];
  writer.SetNodeNameFormat(format);
  if (typeof writer.SetMeshNameFormat === 'function') {
    writer.SetMeshNameFormat(format);
  }
}

function writeGlbInternal(
  oc: OpenCascadeInstance,
  docHandle: OcctDocumentHandle,
  pathInternal: string,
  options: WriteOptions
) {
  const map = createMetadataMap(oc, options.metadata);
  const progress = new oc.Message_ProgressRange_1();
  const file = new oc.TCollection_AsciiString_2(pathInternal);
  const writer = new oc.RWGltf_CafWriter(file, true);
  applyGltfNameFormat(oc, writer, options);
  writer.Perform_2(docHandle, map, progress);
  const data = oc.FS.analyzePath(pathInternal).exists && oc.FS.readFile(pathInternal);
  if (data) {
    oc.FS.unlink(pathInternal);
  }
  return data;
}

function writeGltfInternal(
  oc: OpenCascadeInstance,
  docHandle: OcctDocumentHandle,
  gltfPath: string,
  options: WriteOptions
) {
  const binPath = `${gltfPath.substring(0, gltfPath.lastIndexOf('.'))}.bin`;
  const map = createMetadataMap(oc, options.metadata);
  const progress = new oc.Message_ProgressRange_1();
  const file = new oc.TCollection_AsciiString_2(gltfPath);
  const writer = new oc.RWGltf_CafWriter(file, false);
  applyGltfNameFormat(oc, writer, options);
  writer.Perform_2(docHandle, map, progress);
  const gltfData = oc.FS.analyzePath(gltfPath).exists && oc.FS.readFile(gltfPath);
  const binData = oc.FS.analyzePath(binPath).exists && oc.FS.readFile(binPath);
  if (gltfData) {
    oc.FS.unlink(gltfPath);
  }
  if (binData) {
    oc.FS.unlink(binPath);
  }
  return { gltfData, binData, binPath };
}

function writeObjInternal(
  oc: OpenCascadeInstance,
  docHandle: OcctDocumentHandle,
  pathInternal: string,
  options: WriteOptions
) {
  const map = createMetadataMap(oc, options.metadata);
  const progress = new oc.Message_ProgressRange_1();
  const file = new oc.TCollection_AsciiString_2(pathInternal);
  const writer = new oc.RWObj_CafWriter(file);
  writer.Perform_2(docHandle, map, progress);
  const data = oc.FS.analyzePath(pathInternal).exists && oc.FS.readFile(pathInternal);
  if (data) {
    oc.FS.unlink(pathInternal);
  }
  return data;
}
