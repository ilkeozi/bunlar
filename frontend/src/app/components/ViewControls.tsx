import { memo } from 'react';
import { useAtomStore } from '../state/useAtomStore';

export const ViewControls = memo(function ViewControls() {
  const view = useAtomStore((state) => state.view);
  const updateView = useAtomStore((state) => state.updateView);

  return (
    <section className="panel__toggles">
      <label className="toggle">
        <input
          type="checkbox"
          checked={view.autoRotate}
          onChange={(event) => updateView({ autoRotate: event.target.checked })}
        />
        <span>Auto-rotate camera</span>
      </label>
      <label className="toggle">
        <input
          type="checkbox"
          checked={view.showElectronTrails}
          onChange={(event) => updateView({ showElectronTrails: event.target.checked })}
        />
        <span>Show electron trails</span>
      </label>
    </section>
  );
});
