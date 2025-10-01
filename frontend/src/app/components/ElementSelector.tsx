import { memo } from 'react';
import { ELEMENTS } from '../data/elements';
import { useAtomStore } from '../state/useAtomStore';

export const ElementSelector = memo(function ElementSelector() {
  const selectedSymbol = useAtomStore((state) => state.selectedSymbol);
  const selectElement = useAtomStore((state) => state.selectElement);

  return (
    <div className="panel__section">
      <label className="panel__label" htmlFor="element-select">
        Element
      </label>
      <select
        id="element-select"
        className="panel__select"
        value={selectedSymbol}
        onChange={(event) => selectElement(event.target.value)}
      >
        {ELEMENTS.map((item) => (
          <option key={item.symbol} value={item.symbol}>
            {item.atomicNumber}. {item.name} ({item.symbol})
          </option>
        ))}
      </select>
    </div>
  );
});
