import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ElementSelector } from '../../../components/ElementSelector';
import { ElementStats } from '../../../components/ElementStats';
import { ViewControls } from '../../../components/ViewControls';
import { AtomCanvas } from '../../../features/chemistry/visualizer/AtomCanvas';
import { DEFAULT_ELEMENT, buildElectronShells, estimateNucleusRadius, getElementBySymbol } from '../../../data/elements';
import { useAtomStore } from '../../../state/useAtomStore';
import { useTranslation } from '../../../i18n/useTranslation';

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

export function AtomicVisualizerPage() {
  const selectedSymbol = useAtomStore((state) => state.selectedSymbol);
  const { t } = useTranslation();

  const element = useMemo(() => {
    return getElementBySymbol(selectedSymbol) ?? DEFAULT_ELEMENT;
  }, [selectedSymbol]);

  const nucleusRadius = useMemo(() => estimateNucleusRadius(element), [element]);

  const shells = useMemo(() => buildElectronShells(element.electrons, nucleusRadius), [element, nucleusRadius]);

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <Link to="/subjects/chemistry" className="text-xs font-semibold uppercase tracking-wide text-primary/80">
          ← {t('atomicVisualizer.back')}
        </Link>
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">{t('atomicVisualizer.title')}</h2>
        <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
          {t('atomicVisualizer.subtitle')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>{t('atomicVisualizer.card.title')}</CardTitle>
          <CardDescription>{t('atomicVisualizer.card.description')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="rounded-2xl border border-border/60 bg-background/70 p-4 backdrop-blur">
            <ElementSelector />
          </div>

          <div className="flex flex-1 flex-col gap-7 xl:flex-row">
            <aside className="flex w-full flex-shrink-0 flex-col gap-6 xl:max-w-sm">
              <ElementStats element={element} shells={shells} />
              <ViewControls />
            </aside>
            <section className="relative flex flex-1 min-h-[540px] overflow-hidden rounded-3xl border border-border/60 bg-gradient-to-br from-slate-900/70 via-slate-950/80 to-slate-950/95 shadow-[inset_0_12px_35px_rgba(5,8,15,0.45)]">
              <AtomCanvas element={element} shells={shells} />
              <footer className="pointer-events-none absolute bottom-6 left-6 flex flex-wrap items-center gap-6 text-slate-200/90">
                <LegendItem color="var(--color-proton)" label={t('legend.proton')} />
                <LegendItem color="var(--color-neutron)" label={t('legend.neutron')} />
                <LegendItem color="var(--color-electron)" label={t('legend.electron')} />
              </footer>
            </section>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
