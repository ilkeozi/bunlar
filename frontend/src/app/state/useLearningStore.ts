import { create } from 'zustand';
import type { SupportedLanguage, TranslationKey } from '../i18n/translations';

export type SubjectId = 'atomicExplorer' | 'periodicTable';

export interface SubjectInfo {
  id: SubjectId;
  titleKey: TranslationKey;
  descriptionKey: TranslationKey;
}

export const SUBJECTS: SubjectInfo[] = [
  {
    id: 'atomicExplorer',
    titleKey: 'subjects.atomicExplorer.title',
    descriptionKey: 'subjects.atomicExplorer.description',
  },
  {
    id: 'periodicTable',
    titleKey: 'subjects.periodicTable.title',
    descriptionKey: 'subjects.periodicTable.description',
  },
];

export const SUPPORTED_LANGUAGES: SupportedLanguage[] = ['en', 'tr'];

interface LearningState {
  language: SupportedLanguage;
  subject: SubjectId;
  setLanguage: (language: SupportedLanguage) => void;
  setSubject: (subject: SubjectId) => void;
}

const DEFAULT_LANGUAGE: SupportedLanguage = 'en';
const DEFAULT_SUBJECT: SubjectId = 'atomicExplorer';

export const useLearningStore = create<LearningState>((set) => ({
  language: DEFAULT_LANGUAGE,
  subject: DEFAULT_SUBJECT,
  setLanguage: (language) => {
    set((state) => (state.language === language ? state : { ...state, language }));
  },
  setSubject: (subject) => {
    set((state) => (state.subject === subject ? state : { ...state, subject }));
  },
}));
