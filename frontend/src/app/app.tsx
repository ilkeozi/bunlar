import { useMemo } from 'react';
import { ElementSelector } from './components/ElementSelector';
import { ElementStats } from './components/ElementStats';
import { ViewControls } from './components/ViewControls';
import { AtomCanvas } from './visualizer/AtomCanvas';
import { DEFAULT_ELEMENT, buildElectronShells, estimateNucleusRadius, getElementBySymbol } from './data/elements';
import { useAtomStore } from './state/useAtomStore';
import { useTranslation } from './i18n/useTranslation';
import { SiteHeader } from './components/SiteHeader';

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
  const selectedSymbol = useAtomStore((state) => state.selectedSymbol);
  const { t } = useTranslation();

  const element = useMemo(() => {
    return getElementBySymbol(selectedSymbol) ?? DEFAULT_ELEMENT;
  }, [selectedSymbol]);

  const nucleusRadius = useMemo(() => estimateNucleusRadius(element), [element]);

  const shells = useMemo(() => buildElectronShells(element.electrons, nucleusRadius), [element, nucleusRadius]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950/95 to-slate-900 text-foreground">
      <SiteHeader />
      <div className="mx-auto flex w-full max-w-[1200px] flex-1 flex-col gap-8 px-6 pb-12 pt-8 sm:px-8 lg:px-10">
        <section id="overview" className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{t('app.title')}</h1>
          <p className="max-w-3xl text-base text-muted-foreground sm:text-lg">{t('app.subtitle')}</p>
        </section>

        <section id="lessons" className="space-y-6">
          <div className="rounded-2xl border border-border/60 bg-background/70 p-4 backdrop-blur">
            <ElementSelector />
          </div>

          <main className="flex flex-1 flex-col gap-7 xl:flex-row">
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
          </main>
        </section>

        <section id="blog" className="rounded-3xl border border-border/60 bg-background/80 p-6 backdrop-blur">
          <div className="space-y-2">
            <h2 className="text-2xl font-semibold tracking-tight">Latest Writing</h2>
            <p className="text-sm text-muted-foreground">
              Case studies and experiments from the lab. Posts will land here as the explorer evolves.
            </p>
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {[1, 2].map((entry) => (
              <article
                key={entry}
                className="rounded-2xl border border-border/40 bg-slate-950/60 p-5 shadow-lg shadow-black/20"
              >
                <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">Coming soon</span>
                <h3 className="mt-2 text-xl font-semibold">Designing immersive science lessons</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Sketch notes, UI explorations, and rendering techniques behind the atomic visualizer experience.
                </p>
              </article>
            ))}
          </div>
        </section>

        <section id="about" className="rounded-3xl border border-border/60 bg-background/80 p-6 backdrop-blur">
          <h2 className="text-2xl font-semibold tracking-tight">About the Explorer</h2>
          <div className="mt-4 space-y-4 text-sm text-muted-foreground">
            <p>
              The Science Explorer is a portfolio-ready playground that blends real-time graphics with approachable lesson
              content. Use it to showcase interactive storytelling, React architecture, and thoughtful UX for STEM topics.
            </p>
            <p>
              Built with Vite, React, Zustand, and tailored components from shadcn/ui, the project highlights clean
              composable patterns, state synchronisation, and immersive visuals powered by three.js.
            </p>
          </div>
        </section>

        <section id="contact" className="rounded-3xl border border-border/60 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent p-6">
          <h2 className="text-2xl font-semibold tracking-tight text-primary">Let&apos;s collaborate</h2>
          <p className="mt-2 text-sm text-primary/80">
            Looking to build experiential learning tools or interactive portfolios? Reach out and let&apos;s create something memorable.
          </p>
          <a
            href="mailto:science-explorer@example.com"
            className="mt-4 inline-flex items-center rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/40 transition hover:bg-primary/90"
          >
            Contact the team
          </a>
        </section>
      </div>
    </div>
  );
}

export default App;
