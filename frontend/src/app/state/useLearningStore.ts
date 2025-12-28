import { create } from 'zustand';
import type { SupportedLanguage } from '../i18n/translations';

export const SUPPORTED_LANGUAGES: SupportedLanguage[] = ['en', 'tr'];

interface LearningState {
  language: SupportedLanguage;
  setLanguage: (language: SupportedLanguage) => void;
}

const DEFAULT_LANGUAGE: SupportedLanguage = 'en';

export const useLearningStore = create<LearningState>((set) => ({
  language: DEFAULT_LANGUAGE,
  setLanguage: (language) => {
    set((state) => (state.language === language ? state : { ...state, language }));
  },
}));
