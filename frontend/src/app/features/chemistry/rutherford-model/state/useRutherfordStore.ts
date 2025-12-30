import { create } from 'zustand';
import { DEFAULT_ELEMENT, ELEMENTS } from '../../../../data/elements';

export interface RutherfordViewSettings {
  autoRotate: boolean;
  rotateAtom: boolean;
  freezeMotion: boolean;
  showElectronTrails: boolean;
}

interface RutherfordState {
  selectedSymbol: string;
  view: RutherfordViewSettings;
  selectElement: (symbol: string) => void;
  updateView: (settings: Partial<RutherfordViewSettings>) => void;
}

const DEFAULT_VIEW: RutherfordViewSettings = {
  autoRotate: true,
  rotateAtom: false,
  freezeMotion: false,
  showElectronTrails: true,
};

const DEFAULT_SYMBOL = DEFAULT_ELEMENT.symbol;

export const useRutherfordStore = create<RutherfordState>((set) => ({
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

export const resetRutherfordStore = () => {
  useRutherfordStore.setState((state) => ({
    ...state,
    selectedSymbol: DEFAULT_SYMBOL,
    view: { ...DEFAULT_VIEW },
  }));
};
