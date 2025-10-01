import { memo } from 'react';
import type { ElementDetails, ElectronShell } from '../data/elements';

interface ElementStatsProps {
  element: ElementDetails;
  shells: ElectronShell[];
}

export const ElementStats = memo(function ElementStats({ element, shells }: ElementStatsProps) {

  return (
    <section className="panel__card">
      <header className="panel__header">
        <h2>{element.name}</h2>
        <p>{element.category}</p>
      </header>

      <dl className="panel__stats">
        <div>
          <dt>Atomic number</dt>
          <dd>{element.atomicNumber}</dd>
        </div>
        <div>
          <dt>Atomic mass</dt>
          <dd>{element.atomicMass.toFixed(3)}</dd>
        </div>
        <div>
          <dt>Protons</dt>
          <dd>{element.protons}</dd>
        </div>
        <div>
          <dt>Neutrons</dt>
          <dd>{element.neutrons}</dd>
        </div>
        <div>
          <dt>Electrons</dt>
          <dd>{element.electrons}</dd>
        </div>
      </dl>

      <h3>Electron shells</h3>
      <ul className="panel__shells">
        {shells.map((shell) => (
          <li key={shell.index}>
            <span>n = {shell.index + 1}</span>
            <span className="panel__shell-count">
              {shell.electrons}
              <small>/{shell.capacity}</small>
            </span>
            <div className="panel__shell-bar">
              <span style={{ width: `${shell.occupancyRatio * 100}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
});
