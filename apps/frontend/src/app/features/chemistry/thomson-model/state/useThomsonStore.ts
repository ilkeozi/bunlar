import { create } from 'zustand';
import { DEFAULT_ELEMENT, ELEMENTS } from '../../../../data/elements';

export interface ThomsonViewSettings {
  autoRotate: boolean;
  rotateAtom: boolean;
  freezeMotion: boolean;
  showPositiveSphere: boolean;
  cutawaySphere: boolean;
}

interface ThomsonState {
  selectedSymbol: string;
  view: ThomsonViewSettings;
  selectElement: (symbol: string) => void;
  updateView: (settings: Partial<ThomsonViewSettings>) => void;
}

const DEFAULT_VIEW: ThomsonViewSettings = {
  autoRotate: true,
  rotateAtom: false,
  freezeMotion: false,
  showPositiveSphere: true,
  cutawaySphere: true,
};

const DEFAULT_SYMBOL = DEFAULT_ELEMENT.symbol;

export const useThomsonStore = create<ThomsonState>((set) => ({
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

export const resetThomsonStore = () => {
  useThomsonStore.setState((state) => ({
    ...state,
    selectedSymbol: DEFAULT_SYMBOL,
    view: { ...DEFAULT_VIEW },
  }));
};
