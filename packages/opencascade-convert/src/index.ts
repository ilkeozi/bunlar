export {
  OpenCascadeConverter,
  createConverter,
  createIsolatedConverter,
  convertFile,
  convertBuffer,
} from './converter';

export { getOpenCascade, loadOpenCascade } from './occt/loader';
export { resolveInputFormat, resolveOutputFormat } from './core/formats';
export { DEFAULT_NAME_FORMAT, NAME_FORMAT_KEYS, resolveNameFormatKey } from './core/name-format';
export { ConversionError, ValidationError } from './core/errors';

export type {
  AssemblyNode,
  AssemblyNodeKind,
  BinaryData,
  BomExport,
  BomItem,
  BomOccurrence,
  ConvertBufferFileOptions,
  ConvertBufferOptions,
  ConvertBufferResult,
  ConvertFileOptions,
  ConvertOptions,
  ConvertResult,
  InputFormat,
  NodeMap,
  OutputFormat,
  ReadOptions,
  TriangulateOptions,
  WriteOptions,
  LoaderOptions,
  NameFormat,
} from './core/types';
