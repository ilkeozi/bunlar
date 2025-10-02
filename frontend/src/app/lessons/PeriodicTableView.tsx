import { useMemo } from 'react';
import { ELEMENTS, getElementBySymbol } from '../data/elements';
import { useAtomStore } from '../state/useAtomStore';
import { useTranslation } from '../i18n/useTranslation';
import { PeriodicCanvas } from './PeriodicCanvas';
import { cn } from '@/lib/utils';

export function PeriodicTableView() {
  const { t, translateCategory } = useTranslation();
  const selectedSymbol = useAtomStore((state) => state.selectedSymbol);

  const selectedElement = useMemo(() => getElementBySymbol(selectedSymbol), [selectedSymbol]);

  if (!ELEMENTS.length) {
    return (
      <p className="text-sm text-muted-foreground">{t('periodic.empty')}</p>
    );
  }

  return (
    <section className="flex flex-1 flex-col gap-6 rounded-3xl border border-border/60 bg-background/70 p-6 shadow-xl shadow-black/20 backdrop-blur">
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">{t('periodic.title')}</h2>
        <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">{t('periodic.subtitle')}</p>
        <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">
          {t('periodic.hint')}
        </span>
      </header>

      <div
        className={cn(
          'grid flex-1 gap-6',
          selectedElement && 'lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]'
        )}
      >
        <div className="relative flex min-h-[420px] flex-1 overflow-hidden rounded-3xl border border-border/60 bg-slate-950/80 shadow-[inset_0_20px_60px_rgba(4,8,18,0.6)] backdrop-blur-sm lg:min-h-[560px]">
          <PeriodicCanvas />
        </div>

        {selectedElement && (
          <aside className="flex h-full flex-col gap-6 rounded-2xl border border-border/60 bg-card/80 p-6 shadow-lg shadow-black/20">
            <div className="space-y-1">
              <span className="text-sm font-semibold uppercase tracking-wide text-primary">
                Z {selectedElement.atomicNumber}
              </span>
              <h3 className="text-2xl font-semibold tracking-tight">{selectedElement.name}</h3>
              <span className="text-4xl font-bold text-foreground/90">{selectedElement.symbol}</span>
            </div>
            <dl className="grid gap-4 text-sm">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {t('stats.atomicMass')}
                </dt>
                <dd className="mt-1 text-base font-semibold text-foreground">
                  {selectedElement.atomicMass.toFixed(3)}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {t('stats.protons')}
                </dt>
                <dd className="mt-1 text-base font-semibold text-foreground">{selectedElement.protons}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {t('stats.neutrons')}
                </dt>
                <dd className="mt-1 text-base font-semibold text-foreground">{selectedElement.neutrons}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {t('stats.electrons')}
                </dt>
                <dd className="mt-1 text-base font-semibold text-foreground">{selectedElement.electrons}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {t('stats.category')}
                </dt>
                <dd className="mt-1 text-base font-semibold text-foreground">
                  {translateCategory(selectedElement.category)}
                </dd>
              </div>
            </dl>
          </aside>
        )}
      </div>
    </section>
  );
}
