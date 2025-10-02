import { useMemo } from 'react';
import { translate, translateCategory, type TranslationKey, type SupportedLanguage } from './translations';
import { useLearningStore } from '../state/useLearningStore';

interface TranslationUtilities {
  language: SupportedLanguage;
  t: (key: TranslationKey) => string;
  translateCategory: (category: string) => string;
}

export function useTranslation(): TranslationUtilities {
  const language = useLearningStore((state) => state.language);

  return useMemo(() => ({
    language,
    t: (key: TranslationKey) => translate(language, key),
    translateCategory: (category: string) => translateCategory(language, category),
  }), [language]);
}
