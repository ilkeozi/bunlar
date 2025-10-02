export const TRANSLATIONS = {
  en: {
    'app.title': 'Science Explorer',
    'app.subtitle': 'Pick a lesson module to explore atoms or the periodic table together.',
    'app.language': 'Language',
    'app.subject': 'Lesson',
    'legend.proton': 'Proton',
    'legend.neutron': 'Neutron',
    'legend.electron': 'Electron',
    'subjects.atomicExplorer.title': 'Atomic Explorer',
    'subjects.atomicExplorer.description': 'Visualise atoms in 3D, adjust camera controls, and highlight electron shells.',
    'subjects.periodicTable.title': 'Periodic Table',
    'subjects.periodicTable.description': 'Browse elemental properties, categories, and quick facts for revision.',
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
    'periodic.title': 'Periodic Table',
    'periodic.subtitle': 'Click an element to inspect it inside the Atomic Explorer.',
    'periodic.hint': 'Rotate, zoom, and click a shape to inspect its element.',
    'periodic.empty': 'Periodic table data unavailable.',
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
    'app.subtitle': 'Aile dersi icin atomlari veya periyodik tabloyu birlikte inceleyin.',
    'app.language': 'Dil',
    'app.subject': 'Konu',
    'legend.proton': 'Proton',
    'legend.neutron': 'Notron',
    'legend.electron': 'Elektron',
    'subjects.atomicExplorer.title': 'Atom Kesifi',
    'subjects.atomicExplorer.description': 'Uc boyutlu atomlari goruntuleyin, kamerayi kontrol edin ve elektron katmanlarini inceleyin.',
    'subjects.periodicTable.title': 'Periyodik Tablo',
    'subjects.periodicTable.description': 'Element ozelliklerini ve kategorilerini hizli tekrar icin inceleyin.',
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
    'periodic.title': 'Periyodik Tablo',
    'periodic.subtitle': 'Bir elementi secerek Atom Kesifi icinde inceleyin.',
    'periodic.hint': 'Sekli dondurup yaklastirin ve element bilgisi icin tiklayin.',
    'periodic.empty': 'Periyodik tablo verisi mevcut degil.',
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
