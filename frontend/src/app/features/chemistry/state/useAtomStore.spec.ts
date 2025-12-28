import { beforeEach, describe, expect, it } from 'vitest';
import { useAtomStore, resetAtomStore } from './useAtomStore';
import {
  DEFAULT_ELEMENT,
  ELEMENTS,
  buildElectronShells,
  estimateNucleusRadius,
  getElementBySymbol,
} from '../../../data/elements';

describe('useAtomStore', () => {
  beforeEach(() => {
    resetAtomStore();
  });

  it('selectElement updates the selected symbol when valid', () => {
    const carbon = ELEMENTS.find((element) => element.symbol === 'C');
    expect(carbon).toBeDefined();

    useAtomStore.getState().selectElement('C');

    const state = useAtomStore.getState();
    expect(state.selectedSymbol).toBe('C');

    const selectedElement = getElementBySymbol(state.selectedSymbol) ?? DEFAULT_ELEMENT;
    const nucleusRadius = estimateNucleusRadius(selectedElement);
    const shells = buildElectronShells(selectedElement.electrons, nucleusRadius);

    const totalElectrons = shells.reduce((sum, shell) => sum + shell.electrons, 0);
    expect(totalElectrons).toBe(selectedElement.electrons);
  });

  it('ignores unknown element symbols', () => {
    useAtomStore.getState().selectElement('Unobtanium');
    expect(useAtomStore.getState().selectedSymbol).toBe(DEFAULT_ELEMENT.symbol);
  });

  it('updateView merges interaction flags without resetting others', () => {
    const initialView = useAtomStore.getState().view;

    useAtomStore.getState().updateView({ autoRotate: false });
    expect(useAtomStore.getState().view.autoRotate).toBe(false);
    expect(useAtomStore.getState().view.showElectronTrails).toBe(initialView.showElectronTrails);

    useAtomStore.getState().updateView({ showElectronTrails: false });
    const currentView = useAtomStore.getState().view;
    expect(currentView.autoRotate).toBe(false);
    expect(currentView.showElectronTrails).toBe(false);
  });
});
