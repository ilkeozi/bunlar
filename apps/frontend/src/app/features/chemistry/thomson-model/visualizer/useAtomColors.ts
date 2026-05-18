import { useMemo } from 'react';

export interface AtomColorPalette {
  background: string;
  proton: string;
  neutron: string;
  electron: string;
  nucleusGlow: string;
  electronOrbit: string;
}

const FALLBACK_PALETTE: AtomColorPalette = {
  background: '#05070d',
  proton: '#ff6b4a',
  neutron: '#8aa8ff',
  electron: '#58d1ff',
  nucleusGlow: '#ffddb3',
  electronOrbit: '#2b9dff',
};

function readColorVariable(variableName: string, fallback: string): string {
  if (typeof window === 'undefined') {
    return fallback;
  }

  const root = document.documentElement;
  const value = getComputedStyle(root).getPropertyValue(variableName).trim();
  return value || fallback;
}

export function useAtomColors(): AtomColorPalette {
  return useMemo(() => {
    if (typeof window === 'undefined') {
      return FALLBACK_PALETTE;
    }

    return {
      background: readColorVariable('--color-scene-background', FALLBACK_PALETTE.background),
      proton: readColorVariable('--color-proton', FALLBACK_PALETTE.proton),
      neutron: readColorVariable('--color-neutron', FALLBACK_PALETTE.neutron),
      electron: readColorVariable('--color-electron', FALLBACK_PALETTE.electron),
      nucleusGlow: readColorVariable('--color-nucleus-glow', FALLBACK_PALETTE.nucleusGlow),
      electronOrbit: readColorVariable('--color-electron-orbit', FALLBACK_PALETTE.electronOrbit),
    };
  }, []);
}
