export const TRANSLATIONS = {
  en: {
    'app.title': 'Science Explorer',
    'app.subtitle': 'Explore atoms and their structure in the Atomic Explorer.',
    'app.language': 'Language',
    'legend.proton': 'Proton',
    'legend.neutron': 'Neutron',
    'legend.electron': 'Electron',
    'element.label': 'Element',
    'stats.atomicNumber': 'Atomic number',
    'stats.atomicMass': 'Atomic mass',
    'stats.protons': 'Protons',
    'stats.neutrons': 'Neutrons',
    'stats.electrons': 'Electrons',
    'stats.category': 'Category',
    'stats.shells': 'Electron shells',
    'controls.autoRotate': 'Auto-rotate camera',
    'controls.showTrails': 'Show electron trails',
    'category.Nonmetal': 'Nonmetal',
    'category.Noble gas': 'Noble gas',
    'category.Alkali metal': 'Alkali metal',
    'category.Alkaline earth metal': 'Alkaline earth metal',
    'category.Metalloid': 'Metalloid',
    'category.Halogen': 'Halogen',
    'category.Post-transition metal': 'Post-transition metal',
    'category.Transition metal': 'Transition metal',
    'category.Lanthanide': 'Lanthanide',
    'category.Actinide': 'Actinide',
  },
  tr: {
    'app.title': 'Bilim Kesifi',
    'app.subtitle': 'Atom Kesifi ile atomlari ve yapilarini kesfedin.',
    'app.language': 'Dil',
    'legend.proton': 'Proton',
    'legend.neutron': 'Notron',
    'legend.electron': 'Elektron',
    'element.label': 'Element',
    'stats.atomicNumber': 'Atom numarasi',
    'stats.atomicMass': 'Atom kutlesi',
    'stats.protons': 'Proton',
    'stats.neutrons': 'Notron',
    'stats.electrons': 'Elektron',
    'stats.category': 'Kategori',
    'stats.shells': 'Elektron katmanlari',
    'controls.autoRotate': 'Kamerayi otomatik dondur',
    'controls.showTrails': 'Elektron izlerini goster',
    'category.Nonmetal': 'Ametal',
    'category.Noble gas': 'Soy gaz',
    'category.Alkali metal': 'Alkali metal',
    'category.Alkaline earth metal': 'Toprak alkali metal',
    'category.Metalloid': 'Yari metal',
    'category.Halogen': 'Halojen',
    'category.Post-transition metal': 'Gecis sonrasi metal',
    'category.Transition metal': 'Gecis metali',
    'category.Lanthanide': 'Lantanit',
    'category.Actinide': 'Aktinit',
  },
} as const;

export type SupportedLanguage = keyof typeof TRANSLATIONS;

type TranslationTable = (typeof TRANSLATIONS)['en'];

export type TranslationKey = keyof TranslationTable;

const CATEGORY_KEY_MAP: Record<string, TranslationKey> = {
  'Nonmetal': 'category.Nonmetal',
  'Noble gas': 'category.Noble gas',
  'Alkali metal': 'category.Alkali metal',
  'Alkaline earth metal': 'category.Alkaline earth metal',
  'Metalloid': 'category.Metalloid',
  'Halogen': 'category.Halogen',
  'Post-transition metal': 'category.Post-transition metal',
  'Transition metal': 'category.Transition metal',
  Lanthanide: 'category.Lanthanide',
  Actinide: 'category.Actinide',
};

export function translate(language: SupportedLanguage, key: TranslationKey): string {
  const dictionary = TRANSLATIONS[language];
  if (dictionary && key in dictionary) {
    return dictionary[key];
  }

  return TRANSLATIONS.en[key];
}

export function translateCategory(language: SupportedLanguage, category: string): string {
  const match = CATEGORY_KEY_MAP[category];
  if (match) {
    return translate(language, match);
  }
  return category;
}
