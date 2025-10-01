import { useMemo } from 'react';
import { ElementSelector } from './components/ElementSelector';
import { ElementStats } from './components/ElementStats';
import { ViewControls } from './components/ViewControls';
import { AtomCanvas } from './visualizer/AtomCanvas';
import { DEFAULT_ELEMENT, buildElectronShells, estimateNucleusRadius, getElementBySymbol } from './data/elements';
import { useAtomStore } from './state/useAtomStore';

export function App() {
  const selectedSymbol = useAtomStore((state) => state.selectedSymbol);

  const element = useMemo(() => {
    return getElementBySymbol(selectedSymbol) ?? DEFAULT_ELEMENT;
  }, [selectedSymbol]);

  const nucleusRadius = useMemo(() => estimateNucleusRadius(element), [element]);

  const shells = useMemo(() => buildElectronShells(element.electrons, nucleusRadius), [element, nucleusRadius]);

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1>Atomic Explorer</h1>
          <p className="app__tagline">
            Navigate quantum-inspired atom models with interactive lighting and future-ready controls.
          </p>
        </div>
        <ElementSelector />
      </header>

      <main className="app__content">
        <aside className="app__sidebar">
          <ElementStats element={element} shells={shells} />
          <ViewControls />
        </aside>
        <section className="app__stage">
          <AtomCanvas element={element} shells={shells} />
          <footer className="app__legend">
            <div><span className="legend legend--proton" />Proton</div>
            <div><span className="legend legend--neutron" />Neutron</div>
            <div><span className="legend legend--electron" />Electron</div>
          </footer>
        </section>
      </main>
    </div>
  );
}

export default App;
