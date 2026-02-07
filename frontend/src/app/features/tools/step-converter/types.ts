import type { FormEvent } from 'react';
import type { TranslationKey } from '../../../i18n/translations';

export type OutputFormat = 'gltf' | 'glb' | 'obj';
export type ConversionMode = 'basic' | 'advanced';

export type StepConverterWorkerStage =
  | 'parsing'
  | 'meshing'
  | 'writing'
  | 'metadata'
  | 'packaging';

export type StepConverterErrorCode =
  | 'FILE_TOO_LARGE'
  | 'UNSUPPORTED_EXTENSION'
  | 'INVALID_STEP'
  | 'UNSUPPORTED_STEP_CONTENT'
  | 'UNITS_SCALE_MISMATCH'
  | 'WASM_LOAD_FAILED'
  | 'CONVERSION_FAILED'
  | 'METADATA_FAILED'
  | 'GLB_PATCH_FAILED'
  | 'ZIP_FAILED'
  | 'OUT_OF_MEMORY';

export type StepConverterError = {
  code: StepConverterErrorCode;
  message: string;
  detail?: Record<string, unknown>;
};

export type StepConverterConversionWarning = {
  code: string;
  message: string;
  detail?: Record<string, unknown>;
};

export type StepConverterMeshStats = {
  triangles: number;
  meshCount: number;
  nodeCount: number;
  primitiveCount: number;
  nodesWithMeshCount: number;
  primitivesWithPositionCount: number;
};

export type RequestState = 'idle' | 'loading' | 'success' | 'error';
export type RequestStatus =
  | { state: 'idle' }
  | { state: 'loading'; stage?: StepConverterWorkerStage }
  | { state: 'success' }
  | { state: 'error'; error: StepConverterError };

export type DownloadLink = {
  url: string;
  name: string;
};

export type TranslateFn = (key: TranslationKey) => string;

export type StepConverterController = {
  file: File | null;
  mode: ConversionMode;
  format: OutputFormat;
  linDeflection: string;
  angDeflection: string;
  relative: boolean;
  parallel: boolean;
  includeBom: boolean;
  includeNodeMap: boolean;
  status: RequestStatus;
  metadataStatus: RequestStatus;
  download: DownloadLink | null;
  meshStats: StepConverterMeshStats | null;
  conversionWarnings: StepConverterConversionWarning[];
  bom: DownloadLink | null;
  nodeMap: DownloadLink | null;
  hasInvalidNumbers: boolean;
  isAdvanced: boolean;
  onFileChange: (file: File | null) => void;
  onModeChange: (mode: ConversionMode) => void;
  onFormatChange: (format: OutputFormat) => void;
  onLinDeflectionChange: (value: string) => void;
  onAngDeflectionChange: (value: string) => void;
  onRelativeChange: (value: boolean) => void;
  onParallelChange: (value: boolean) => void;
  onIncludeBomChange: (value: boolean) => void;
  onIncludeNodeMapChange: (value: boolean) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onReset: () => void;
  onCancel: () => void;
};
