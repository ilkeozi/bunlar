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
