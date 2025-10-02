import { useMemo } from 'react';
import { ElementSelector } from './components/ElementSelector';
import { ElementStats } from './components/ElementStats';
import { ViewControls } from './components/ViewControls';
import { AtomCanvas } from './visualizer/AtomCanvas';
import { DEFAULT_ELEMENT, buildElectronShells, estimateNucleusRadius, getElementBySymbol } from './data/elements';
import { useAtomStore } from './state/useAtomStore';
import { LanguageSelector } from './components/LanguageSelector';
import { SubjectSelector } from './components/SubjectSelector';
import { useLearningStore } from './state/useLearningStore';
import { PeriodicTableView } from './lessons/PeriodicTableView';
import { useTranslation } from './i18n/useTranslation';
import { cn } from '@/lib/utils';

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-2 text-xs font-medium">
      <span
        className="h-3 w-3 rounded-full"
        style={{ backgroundColor: color, boxShadow: `0 0 12px ${color}` }}
      />
      {label}
    </span>
  );
}

export function App() {
  const subject = useLearningStore((state) => state.subject);
  const selectedSymbol = useAtomStore((state) => state.selectedSymbol);
  const { t } = useTranslation();

  const element = useMemo(() => {
    return getElementBySymbol(selectedSymbol) ?? DEFAULT_ELEMENT;
  }, [selectedSymbol]);

  const nucleusRadius = useMemo(() => estimateNucleusRadius(element), [element]);

  const shells = useMemo(() => buildElectronShells(element.electrons, nucleusRadius), [element, nucleusRadius]);

  const isAtomicExplorer = subject === 'atomicExplorer';

  return (
    <div className="flex min-h-screen flex-col gap-7 p-6 text-foreground sm:p-8 lg:p-10">
      <header className="flex flex-wrap items-start justify-between gap-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{t('app.title')}</h1>
          <p className="max-w-3xl text-base text-muted-foreground sm:text-lg">{t('app.subtitle')}</p>
        </div>
        <div className="flex items-center gap-3">
          <LanguageSelector />
        </div>
      </header>

      <SubjectSelector />

      {isAtomicExplorer && (
        <div className="rounded-2xl border border-border/60 bg-background/70 p-4 backdrop-blur">
          <ElementSelector />
        </div>
      )}

      <main
        className={cn(
          'flex-1',
          isAtomicExplorer ? 'flex flex-col gap-7 xl:flex-row' : 'flex flex-col'
        )}
      >
        {isAtomicExplorer ? (
          <>
            <aside className="flex w-full flex-shrink-0 flex-col gap-6 xl:max-w-sm">
              <ElementStats element={element} shells={shells} />
              <ViewControls />
            </aside>
            <section className="relative flex flex-1 overflow-hidden rounded-3xl border border-border/60 bg-gradient-to-br from-slate-900/70 via-slate-950/80 to-slate-950/95 shadow-[inset_0_12px_35px_rgba(5,8,15,0.45)] min-h-[540px]">
              <AtomCanvas element={element} shells={shells} />
              <footer className="pointer-events-none absolute bottom-6 left-6 flex flex-wrap items-center gap-6 text-slate-200/90">
                <LegendItem color="var(--color-proton)" label={t('legend.proton')} />
                <LegendItem color="var(--color-neutron)" label={t('legend.neutron')} />
                <LegendItem color="var(--color-electron)" label={t('legend.electron')} />
              </footer>
            </section>
          </>
        ) : (
          <PeriodicTableView />
        )}
      </main>
    </div>
  );
}

export default App;
