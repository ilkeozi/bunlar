import { create } from 'zustand';
import { DEFAULT_ELEMENT, ELEMENTS } from '../../../data/elements';

export interface AtomViewSettings {
  showElectronTrails: boolean;
  autoRotate: boolean;
  rotateAtom: boolean;
  tiltedOrbits: boolean;
  freezeMotion: boolean;
}

interface AtomState {
  selectedSymbol: string;
  view: AtomViewSettings;
  selectElement: (symbol: string) => void;
  updateView: (settings: Partial<AtomViewSettings>) => void;
}

const DEFAULT_VIEW: AtomViewSettings = {
  showElectronTrails: true,
  autoRotate: true,
  rotateAtom: false,
  tiltedOrbits: false,
  freezeMotion: false,
};

const DEFAULT_SYMBOL = DEFAULT_ELEMENT.symbol;

export const useAtomStore = create<AtomState>((set) => ({
  selectedSymbol: DEFAULT_SYMBOL,
  view: { ...DEFAULT_VIEW },
  selectElement: (symbol) => {
    if (!ELEMENTS.find((item) => item.symbol === symbol)) {
      return;
    }

    set((state) => {
      if (state.selectedSymbol === symbol) {
        return state;
      }
      return {
        ...state,
        selectedSymbol: symbol,
      };
    });
  },
  updateView: (settings) => {
    set((state) => ({
      ...state,
      view: {
        ...state.view,
        ...settings,
      },
    }));
  },
}));

export const resetAtomStore = () => {
  useAtomStore.setState((state) => ({
    ...state,
    selectedSymbol: DEFAULT_SYMBOL,
    view: { ...DEFAULT_VIEW },
  }));
};
