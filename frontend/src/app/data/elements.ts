export interface ElementInfo {
  symbol: string;
  name: string;
  atomicNumber: number;
  atomicMass: number;
  category: string;
}

export type ElementPhase = 'solid' | 'liquid' | 'gas';

export interface ElementDetails extends ElementInfo {
  protons: number;
  neutrons: number;
  electrons: number;
  phase: ElementPhase;
  isRadioactive: boolean;
  radioactivityLevel: number;
}

const RAW_ELEMENTS: ElementInfo[] = [
  { symbol: 'H', name: 'Hydrogen', atomicNumber: 1, atomicMass: 1.008, category: 'Nonmetal' },
  { symbol: 'He', name: 'Helium', atomicNumber: 2, atomicMass: 4.0026, category: 'Noble gas' },
  { symbol: 'Li', name: 'Lithium', atomicNumber: 3, atomicMass: 6.94, category: 'Alkali metal' },
  { symbol: 'Be', name: 'Beryllium', atomicNumber: 4, atomicMass: 9.0122, category: 'Alkaline earth metal' },
  { symbol: 'B', name: 'Boron', atomicNumber: 5, atomicMass: 10.81, category: 'Metalloid' },
  { symbol: 'C', name: 'Carbon', atomicNumber: 6, atomicMass: 12.011, category: 'Nonmetal' },
  { symbol: 'N', name: 'Nitrogen', atomicNumber: 7, atomicMass: 14.007, category: 'Nonmetal' },
  { symbol: 'O', name: 'Oxygen', atomicNumber: 8, atomicMass: 15.999, category: 'Nonmetal' },
  { symbol: 'F', name: 'Fluorine', atomicNumber: 9, atomicMass: 18.998, category: 'Halogen' },
  { symbol: 'Ne', name: 'Neon', atomicNumber: 10, atomicMass: 20.1797, category: 'Noble gas' },
  { symbol: 'Na', name: 'Sodium', atomicNumber: 11, atomicMass: 22.9898, category: 'Alkali metal' },
  { symbol: 'Mg', name: 'Magnesium', atomicNumber: 12, atomicMass: 24.305, category: 'Alkaline earth metal' },
  { symbol: 'Al', name: 'Aluminium', atomicNumber: 13, atomicMass: 26.9815, category: 'Post-transition metal' },
  { symbol: 'Si', name: 'Silicon', atomicNumber: 14, atomicMass: 28.085, category: 'Metalloid' },
  { symbol: 'P', name: 'Phosphorus', atomicNumber: 15, atomicMass: 30.9738, category: 'Nonmetal' },
  { symbol: 'S', name: 'Sulfur', atomicNumber: 16, atomicMass: 32.06, category: 'Nonmetal' },
  { symbol: 'Cl', name: 'Chlorine', atomicNumber: 17, atomicMass: 35.45, category: 'Halogen' },
  { symbol: 'Ar', name: 'Argon', atomicNumber: 18, atomicMass: 39.948, category: 'Noble gas' },
  { symbol: 'K', name: 'Potassium', atomicNumber: 19, atomicMass: 39.0983, category: 'Alkali metal' },
  { symbol: 'Ca', name: 'Calcium', atomicNumber: 20, atomicMass: 40.078, category: 'Alkaline earth metal' },
  { symbol: 'Sc', name: 'Scandium', atomicNumber: 21, atomicMass: 44.9559, category: 'Transition metal' },
  { symbol: 'Ti', name: 'Titanium', atomicNumber: 22, atomicMass: 47.867, category: 'Transition metal' },
  { symbol: 'V', name: 'Vanadium', atomicNumber: 23, atomicMass: 50.9415, category: 'Transition metal' },
  { symbol: 'Cr', name: 'Chromium', atomicNumber: 24, atomicMass: 51.9961, category: 'Transition metal' },
  { symbol: 'Mn', name: 'Manganese', atomicNumber: 25, atomicMass: 54.938, category: 'Transition metal' },
  { symbol: 'Fe', name: 'Iron', atomicNumber: 26, atomicMass: 55.845, category: 'Transition metal' },
  { symbol: 'Co', name: 'Cobalt', atomicNumber: 27, atomicMass: 58.9332, category: 'Transition metal' },
  { symbol: 'Ni', name: 'Nickel', atomicNumber: 28, atomicMass: 58.6934, category: 'Transition metal' },
  { symbol: 'Cu', name: 'Copper', atomicNumber: 29, atomicMass: 63.546, category: 'Transition metal' },
  { symbol: 'Zn', name: 'Zinc', atomicNumber: 30, atomicMass: 65.38, category: 'Transition metal' },
  { symbol: 'Ga', name: 'Gallium', atomicNumber: 31, atomicMass: 69.723, category: 'Post-transition metal' },
  { symbol: 'Ge', name: 'Germanium', atomicNumber: 32, atomicMass: 72.63, category: 'Metalloid' },
  { symbol: 'As', name: 'Arsenic', atomicNumber: 33, atomicMass: 74.9216, category: 'Metalloid' },
  { symbol: 'Se', name: 'Selenium', atomicNumber: 34, atomicMass: 78.971, category: 'Nonmetal' },
  { symbol: 'Br', name: 'Bromine', atomicNumber: 35, atomicMass: 79.904, category: 'Halogen' },
  { symbol: 'Kr', name: 'Krypton', atomicNumber: 36, atomicMass: 83.798, category: 'Noble gas' },
  { symbol: 'Rb', name: 'Rubidium', atomicNumber: 37, atomicMass: 85.4678, category: 'Alkali metal' },
  { symbol: 'Sr', name: 'Strontium', atomicNumber: 38, atomicMass: 87.62, category: 'Alkaline earth metal' },
  { symbol: 'Y', name: 'Yttrium', atomicNumber: 39, atomicMass: 88.9059, category: 'Transition metal' },
  { symbol: 'Zr', name: 'Zirconium', atomicNumber: 40, atomicMass: 91.224, category: 'Transition metal' },
  { symbol: 'Nb', name: 'Niobium', atomicNumber: 41, atomicMass: 92.9064, category: 'Transition metal' },
  { symbol: 'Mo', name: 'Molybdenum', atomicNumber: 42, atomicMass: 95.95, category: 'Transition metal' },
  { symbol: 'Tc', name: 'Technetium', atomicNumber: 43, atomicMass: 98, category: 'Transition metal' },
  { symbol: 'Ru', name: 'Ruthenium', atomicNumber: 44, atomicMass: 101.07, category: 'Transition metal' },
  { symbol: 'Rh', name: 'Rhodium', atomicNumber: 45, atomicMass: 102.9055, category: 'Transition metal' },
  { symbol: 'Pd', name: 'Palladium', atomicNumber: 46, atomicMass: 106.42, category: 'Transition metal' },
  { symbol: 'Ag', name: 'Silver', atomicNumber: 47, atomicMass: 107.8682, category: 'Transition metal' },
  { symbol: 'Cd', name: 'Cadmium', atomicNumber: 48, atomicMass: 112.414, category: 'Transition metal' },
  { symbol: 'In', name: 'Indium', atomicNumber: 49, atomicMass: 114.818, category: 'Post-transition metal' },
  { symbol: 'Sn', name: 'Tin', atomicNumber: 50, atomicMass: 118.71, category: 'Post-transition metal' },
  { symbol: 'Sb', name: 'Antimony', atomicNumber: 51, atomicMass: 121.76, category: 'Metalloid' },
  { symbol: 'Te', name: 'Tellurium', atomicNumber: 52, atomicMass: 127.6, category: 'Metalloid' },
  { symbol: 'I', name: 'Iodine', atomicNumber: 53, atomicMass: 126.9045, category: 'Halogen' },
  { symbol: 'Xe', name: 'Xenon', atomicNumber: 54, atomicMass: 131.293, category: 'Noble gas' },
  { symbol: 'Cs', name: 'Cesium', atomicNumber: 55, atomicMass: 132.9055, category: 'Alkali metal' },
  { symbol: 'Ba', name: 'Barium', atomicNumber: 56, atomicMass: 137.327, category: 'Alkaline earth metal' },
  { symbol: 'La', name: 'Lanthanum', atomicNumber: 57, atomicMass: 138.9055, category: 'Lanthanide' },
  { symbol: 'Ce', name: 'Cerium', atomicNumber: 58, atomicMass: 140.116, category: 'Lanthanide' },
  { symbol: 'Pr', name: 'Praseodymium', atomicNumber: 59, atomicMass: 140.9077, category: 'Lanthanide' },
  { symbol: 'Nd', name: 'Neodymium', atomicNumber: 60, atomicMass: 144.242, category: 'Lanthanide' },
  { symbol: 'Pm', name: 'Promethium', atomicNumber: 61, atomicMass: 145, category: 'Lanthanide' },
  { symbol: 'Sm', name: 'Samarium', atomicNumber: 62, atomicMass: 150.36, category: 'Lanthanide' },
  { symbol: 'Eu', name: 'Europium', atomicNumber: 63, atomicMass: 151.964, category: 'Lanthanide' },
  { symbol: 'Gd', name: 'Gadolinium', atomicNumber: 64, atomicMass: 157.25, category: 'Lanthanide' },
  { symbol: 'Tb', name: 'Terbium', atomicNumber: 65, atomicMass: 158.9254, category: 'Lanthanide' },
  { symbol: 'Dy', name: 'Dysprosium', atomicNumber: 66, atomicMass: 162.5, category: 'Lanthanide' },
  { symbol: 'Ho', name: 'Holmium', atomicNumber: 67, atomicMass: 164.9303, category: 'Lanthanide' },
  { symbol: 'Er', name: 'Erbium', atomicNumber: 68, atomicMass: 167.259, category: 'Lanthanide' },
  { symbol: 'Tm', name: 'Thulium', atomicNumber: 69, atomicMass: 168.9342, category: 'Lanthanide' },
  { symbol: 'Yb', name: 'Ytterbium', atomicNumber: 70, atomicMass: 173.045, category: 'Lanthanide' },
  { symbol: 'Lu', name: 'Lutetium', atomicNumber: 71, atomicMass: 174.9668, category: 'Lanthanide' },
  { symbol: 'Hf', name: 'Hafnium', atomicNumber: 72, atomicMass: 178.49, category: 'Transition metal' },
  { symbol: 'Ta', name: 'Tantalum', atomicNumber: 73, atomicMass: 180.9479, category: 'Transition metal' },
  { symbol: 'W', name: 'Tungsten', atomicNumber: 74, atomicMass: 183.84, category: 'Transition metal' },
  { symbol: 'Re', name: 'Rhenium', atomicNumber: 75, atomicMass: 186.207, category: 'Transition metal' },
  { symbol: 'Os', name: 'Osmium', atomicNumber: 76, atomicMass: 190.23, category: 'Transition metal' },
  { symbol: 'Ir', name: 'Iridium', atomicNumber: 77, atomicMass: 192.217, category: 'Transition metal' },
  { symbol: 'Pt', name: 'Platinum', atomicNumber: 78, atomicMass: 195.084, category: 'Transition metal' },
  { symbol: 'Au', name: 'Gold', atomicNumber: 79, atomicMass: 196.9666, category: 'Transition metal' },
  { symbol: 'Hg', name: 'Mercury', atomicNumber: 80, atomicMass: 200.592, category: 'Transition metal' },
  { symbol: 'Tl', name: 'Thallium', atomicNumber: 81, atomicMass: 204.38, category: 'Post-transition metal' },
  { symbol: 'Pb', name: 'Lead', atomicNumber: 82, atomicMass: 207.2, category: 'Post-transition metal' },
  { symbol: 'Bi', name: 'Bismuth', atomicNumber: 83, atomicMass: 208.9804, category: 'Post-transition metal' },
  { symbol: 'Po', name: 'Polonium', atomicNumber: 84, atomicMass: 209, category: 'Metalloid' },
  { symbol: 'At', name: 'Astatine', atomicNumber: 85, atomicMass: 210, category: 'Halogen' },
  { symbol: 'Rn', name: 'Radon', atomicNumber: 86, atomicMass: 222, category: 'Noble gas' },
  { symbol: 'Fr', name: 'Francium', atomicNumber: 87, atomicMass: 223, category: 'Alkali metal' },
  { symbol: 'Ra', name: 'Radium', atomicNumber: 88, atomicMass: 226, category: 'Alkaline earth metal' },
  { symbol: 'Ac', name: 'Actinium', atomicNumber: 89, atomicMass: 227, category: 'Actinide' },
  { symbol: 'Th', name: 'Thorium', atomicNumber: 90, atomicMass: 232.0377, category: 'Actinide' },
  { symbol: 'Pa', name: 'Protactinium', atomicNumber: 91, atomicMass: 231.0359, category: 'Actinide' },
  { symbol: 'U', name: 'Uranium', atomicNumber: 92, atomicMass: 238.0289, category: 'Actinide' },
  { symbol: 'Np', name: 'Neptunium', atomicNumber: 93, atomicMass: 237, category: 'Actinide' },
  { symbol: 'Pu', name: 'Plutonium', atomicNumber: 94, atomicMass: 244, category: 'Actinide' },
  { symbol: 'Am', name: 'Americium', atomicNumber: 95, atomicMass: 243, category: 'Actinide' },
  { symbol: 'Cm', name: 'Curium', atomicNumber: 96, atomicMass: 247, category: 'Actinide' },
  { symbol: 'Bk', name: 'Berkelium', atomicNumber: 97, atomicMass: 247, category: 'Actinide' },
  { symbol: 'Cf', name: 'Californium', atomicNumber: 98, atomicMass: 251, category: 'Actinide' },
  { symbol: 'Es', name: 'Einsteinium', atomicNumber: 99, atomicMass: 252, category: 'Actinide' },
  { symbol: 'Fm', name: 'Fermium', atomicNumber: 100, atomicMass: 257, category: 'Actinide' },
  { symbol: 'Md', name: 'Mendelevium', atomicNumber: 101, atomicMass: 258, category: 'Actinide' },
  { symbol: 'No', name: 'Nobelium', atomicNumber: 102, atomicMass: 259, category: 'Actinide' },
  { symbol: 'Lr', name: 'Lawrencium', atomicNumber: 103, atomicMass: 266, category: 'Actinide' },
  { symbol: 'Rf', name: 'Rutherfordium', atomicNumber: 104, atomicMass: 267, category: 'Transition metal' },
  { symbol: 'Db', name: 'Dubnium', atomicNumber: 105, atomicMass: 268, category: 'Transition metal' },
  { symbol: 'Sg', name: 'Seaborgium', atomicNumber: 106, atomicMass: 269, category: 'Transition metal' },
  { symbol: 'Bh', name: 'Bohrium', atomicNumber: 107, atomicMass: 270, category: 'Transition metal' },
  { symbol: 'Hs', name: 'Hassium', atomicNumber: 108, atomicMass: 269, category: 'Transition metal' },
  { symbol: 'Mt', name: 'Meitnerium', atomicNumber: 109, atomicMass: 278, category: 'Transition metal' },
  { symbol: 'Ds', name: 'Darmstadtium', atomicNumber: 110, atomicMass: 281, category: 'Transition metal' },
  { symbol: 'Rg', name: 'Roentgenium', atomicNumber: 111, atomicMass: 282, category: 'Transition metal' },
  { symbol: 'Cn', name: 'Copernicium', atomicNumber: 112, atomicMass: 285, category: 'Transition metal' },
  { symbol: 'Nh', name: 'Nihonium', atomicNumber: 113, atomicMass: 286, category: 'Post-transition metal' },
  { symbol: 'Fl', name: 'Flerovium', atomicNumber: 114, atomicMass: 289, category: 'Post-transition metal' },
  { symbol: 'Mc', name: 'Moscovium', atomicNumber: 115, atomicMass: 290, category: 'Post-transition metal' },
  { symbol: 'Lv', name: 'Livermorium', atomicNumber: 116, atomicMass: 293, category: 'Post-transition metal' },
  { symbol: 'Ts', name: 'Tennessine', atomicNumber: 117, atomicMass: 294, category: 'Halogen' },
  { symbol: 'Og', name: 'Oganesson', atomicNumber: 118, atomicMass: 294, category: 'Noble gas' },
];

const GAS_ELEMENTS = new Set([
  'H',
  'He',
  'N',
  'O',
  'F',
  'Ne',
  'Cl',
  'Ar',
  'Kr',
  'Xe',
  'Rn',
  'Og',
]);

const LIQUID_ELEMENTS = new Set(['Br', 'Hg']);

const RADIOACTIVE_STATES: Record<string, number> = {
  Tc: 0.55,
  Pm: 0.6,
  Po: 0.72,
  At: 0.75,
  Rn: 0.82,
  Fr: 0.95,
  Ra: 0.9,
  Ac: 0.9,
  Th: 0.75,
  Pa: 0.82,
  U: 0.92,
  Np: 0.93,
  Pu: 0.95,
  Am: 0.96,
  Cm: 0.96,
  Bk: 0.96,
  Cf: 0.97,
  Es: 0.97,
  Fm: 0.97,
  Md: 0.97,
  No: 0.97,
  Lr: 0.97,
  Rf: 0.98,
  Db: 0.98,
  Sg: 0.98,
  Bh: 0.98,
  Hs: 0.98,
  Mt: 0.99,
  Ds: 0.99,
  Rg: 0.99,
  Cn: 0.99,
  Nh: 1,
  Fl: 1,
  Mc: 1,
  Lv: 1,
  Ts: 1,
  Og: 1,
};

const RADIOACTIVE_ELEMENTS = new Set(Object.keys(RADIOACTIVE_STATES));

export const ELEMENTS: ElementDetails[] = RAW_ELEMENTS.map((element) => {
  const protons = element.atomicNumber;
  const electrons = element.atomicNumber;
  const neutrons = Math.max(0, Math.round(element.atomicMass) - element.atomicNumber);
  const phase: ElementPhase = GAS_ELEMENTS.has(element.symbol)
    ? 'gas'
    : LIQUID_ELEMENTS.has(element.symbol)
    ? 'liquid'
    : 'solid';
  const isRadioactive = RADIOACTIVE_ELEMENTS.has(element.symbol);
  const fallbackLevel = element.atomicNumber >= 83 ? Math.min(1, (element.atomicNumber - 78) / 40) : 0.45;
  const radioactivityLevel = isRadioactive ? RADIOACTIVE_STATES[element.symbol] ?? fallbackLevel : 0;

  return {
    ...element,
    protons,
    electrons,
    neutrons,
    phase,
    isRadioactive,
    radioactivityLevel,
  };
});

export const DEFAULT_ELEMENT = ELEMENTS[0];

export const SHELL_CAPACITIES = [2, 8, 18, 32, 32, 18, 8] as const;

export interface ElectronShell {
  index: number;
  capacity: number;
  electrons: number;
  occupancyRatio: number;
  radius: number;
}

export function getElementBySymbol(symbol: string): ElementDetails | undefined {
  return ELEMENTS.find((item) => item.symbol === symbol);
}

export function distributeElectrons(totalElectrons: number): number[] {
  const result: number[] = [];
  let remaining = totalElectrons;

  for (const capacity of SHELL_CAPACITIES) {
    if (remaining <= 0) {
      result.push(0);
      continue;
    }

    const electronsInShell = Math.min(remaining, capacity);
    result.push(electronsInShell);
    remaining -= electronsInShell;
  }

  return result;
}

export function buildElectronShells(totalElectrons: number, nucleusRadius: number): ElectronShell[] {
  const distribution = distributeElectrons(totalElectrons);

  return distribution.map((count, index) => {
    const capacity = SHELL_CAPACITIES[index] ?? SHELL_CAPACITIES[SHELL_CAPACITIES.length - 1];
    const occupancyRatio = capacity ? count / capacity : 0;
    const radius = nucleusRadius + 1.4 + index * 1.05 + occupancyRatio * 0.35;

    return {
      index,
      capacity,
      electrons: count,
      occupancyRatio,
      radius,
    };
  });
}

export function estimateNucleusRadius(element: ElementDetails): number {
  const totalNucleons = element.protons + element.neutrons;
  return Math.max(0.6, Math.cbrt(Math.max(totalNucleons, 1)) * 0.34);
}
