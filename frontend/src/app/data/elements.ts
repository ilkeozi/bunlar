export interface ElementInfo {
  symbol: string;
  name: string;
  atomicNumber: number;
  atomicMass: number;
  category: string;
}

export interface ElementDetails extends ElementInfo {
  protons: number;
  neutrons: number;
  electrons: number;
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
  { symbol: 'Ne', name: 'Neon', atomicNumber: 10, atomicMass: 20.18, category: 'Noble gas' },
  { symbol: 'Na', name: 'Sodium', atomicNumber: 11, atomicMass: 22.99, category: 'Alkali metal' },
  { symbol: 'Mg', name: 'Magnesium', atomicNumber: 12, atomicMass: 24.305, category: 'Alkaline earth metal' },
  { symbol: 'Al', name: 'Aluminium', atomicNumber: 13, atomicMass: 26.982, category: 'Post-transition metal' },
  { symbol: 'Si', name: 'Silicon', atomicNumber: 14, atomicMass: 28.085, category: 'Metalloid' },
  { symbol: 'P', name: 'Phosphorus', atomicNumber: 15, atomicMass: 30.974, category: 'Nonmetal' },
  { symbol: 'S', name: 'Sulfur', atomicNumber: 16, atomicMass: 32.06, category: 'Nonmetal' },
  { symbol: 'Cl', name: 'Chlorine', atomicNumber: 17, atomicMass: 35.45, category: 'Halogen' },
  { symbol: 'Ar', name: 'Argon', atomicNumber: 18, atomicMass: 39.948, category: 'Noble gas' },
  { symbol: 'K', name: 'Potassium', atomicNumber: 19, atomicMass: 39.098, category: 'Alkali metal' },
  { symbol: 'Ca', name: 'Calcium', atomicNumber: 20, atomicMass: 40.078, category: 'Alkaline earth metal' }
];

export const ELEMENTS: ElementDetails[] = RAW_ELEMENTS.map((element) => {
  const protons = element.atomicNumber;
  const electrons = element.atomicNumber;
  const neutrons = Math.max(0, Math.round(element.atomicMass) - element.atomicNumber);

  return {
    ...element,
    protons,
    electrons,
    neutrons,
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
