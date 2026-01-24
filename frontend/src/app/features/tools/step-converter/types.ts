import type { FormEvent } from 'react';
import type { TranslationKey } from '../../../i18n/translations';

export type OutputFormat = 'gltf' | 'glb' | 'obj';
export type ConversionMode = 'basic' | 'advanced';

export type RequestState = 'idle' | 'loading' | 'success' | 'error';
export type RequestStatus = {
  state: RequestState;
  message?: string;
};

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
