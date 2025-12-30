import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { ElementSelector } from '../../../features/chemistry/rutherford-model/components/ElementSelector';
import { ElementStats } from '../../../features/chemistry/rutherford-model/components/ElementStats';
import { ViewControls } from '../../../features/chemistry/rutherford-model/components/ViewControls';
import { RutherfordCanvas } from '../../../features/chemistry/rutherford-model/visualizer/RutherfordCanvas';
import { DEFAULT_ELEMENT, getElementBySymbol } from '../../../data/elements';
import { useRutherfordStore } from '../../../features/chemistry/rutherford-model/state/useRutherfordStore';
import { useTranslation } from '../../../i18n/useTranslation';

export function RutherfordModelPage() {
  const selectedSymbol = useRutherfordStore((state) => state.selectedSymbol);
  const { t } = useTranslation();

  const element = useMemo(() => {
    return getElementBySymbol(selectedSymbol) ?? DEFAULT_ELEMENT;
  }, [selectedSymbol]);

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <Link to="/subjects/chemistry" className="text-xs font-semibold uppercase tracking-wide text-primary/80">
          ← {t('rutherfordModel.back')}
        </Link>
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">{t('rutherfordModel.title')}</h2>
        <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
          {t('rutherfordModel.subtitle')}
        </p>
      </header>

      <div className="space-y-6">
        <div className="rounded-2xl border border-border/60 bg-background/70 p-4 backdrop-blur">
          <ElementSelector />
        </div>

        <div className="flex flex-1 flex-col gap-7 xl:flex-row">
          <aside className="flex w-full flex-shrink-0 flex-col gap-6 xl:max-w-sm">
            <ElementStats element={element} />
            <ViewControls />
          </aside>
          <section className="relative flex flex-1 min-h-[540px] overflow-hidden rounded-3xl border border-border/60 bg-gradient-to-br from-slate-900/70 via-slate-950/80 to-slate-950/95 shadow-[inset_0_12px_35px_rgba(5,8,15,0.45)]">
            <RutherfordCanvas element={element} />
          </section>
        </div>
      </div>
    </div>
  );
}
