import { create } from 'zustand';
import { DEFAULT_ELEMENT, ELEMENTS } from '../../../../data/elements';

export interface DaltonViewSettings {
  autoRotate: boolean;
  rotateAtom: boolean;
  freezeMotion: boolean;
}

interface DaltonState {
  selectedSymbol: string;
  view: DaltonViewSettings;
  selectElement: (symbol: string) => void;
  updateView: (settings: Partial<DaltonViewSettings>) => void;
}

const DEFAULT_VIEW: DaltonViewSettings = {
  autoRotate: true,
  rotateAtom: false,
  freezeMotion: false,
};

const DEFAULT_SYMBOL = DEFAULT_ELEMENT.symbol;

export const useDaltonStore = create<DaltonState>((set) => ({
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

export const resetDaltonStore = () => {
  useDaltonStore.setState((state) => ({
    ...state,
    selectedSymbol: DEFAULT_SYMBOL,
    view: { ...DEFAULT_VIEW },
  }));
};
