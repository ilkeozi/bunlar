import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { AssemblyControlsToggle } from '../../../features/climate-tech/assembly-viewer/components/AssemblyControlsToggle';
import { AssemblyExplorerPanel } from '../../../features/climate-tech/assembly-viewer/components/AssemblyExplorerPanel';
import { AssemblyFileCard } from '../../../features/climate-tech/assembly-viewer/components/AssemblyFileCard';
import { useAssemblyFile } from '../../../features/climate-tech/assembly-viewer/hooks/useAssemblyFile';
import { useAssemblyExplorerStore } from '../../../features/climate-tech/assembly-viewer/state/useAssemblyExplorerStore';
import { AssemblyCanvas } from '../../../features/climate-tech/assembly-viewer/visualizer/AssemblyCanvas';
import { useTranslation } from '../../../i18n/useTranslation';

export function AssemblyViewerPage() {
  const { t } = useTranslation();
  const defaultModelName = t('assemblyViewer.input.placeholder');
  const controlsRef = useRef<OrbitControlsImpl | null>(null);
  const [autoRotate, setAutoRotate] = useState(true);
  const [controlsOpen, setControlsOpen] = useState(false);

  const {
    modelUrl,
    fileName,
    status,
    error,
    isSample,
    metadata,
    setFile,
    resetToSample,
    markReady,
  } = useAssemblyFile(t, '', defaultModelName);

  useEffect(() => {
    useAssemblyExplorerStore.getState().setNodeMap(metadata?.nodeMap ?? null);
  }, [metadata]);

  const handleResetView = () => {
    controlsRef.current?.reset();
    controlsRef.current?.update();
  };

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <Link
          to="/visualizations"
          className="text-xs font-semibold uppercase tracking-wide text-primary/80"
        >
          ← {t('visualizations.back')}
        </Link>
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          {t('climateTech.modules.assemblyViewer.title')}
        </h2>
        <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
          {t('climateTech.modules.assemblyViewer.description')}
        </p>
      </header>

      <div className="flex flex-1 flex-col gap-7 xl:flex-row">
        <div className="flex items-center justify-between xl:hidden">
          <AssemblyControlsToggle
            controlsOpen={controlsOpen}
            onToggle={() => setControlsOpen((open) => !open)}
          />
        </div>
        <aside
          className={`flex w-full flex-shrink-0 flex-col gap-6 xl:max-w-sm ${
            controlsOpen ? 'flex' : 'hidden'
          } xl:flex`}
        >
          <AssemblyFileCard
            fileName={fileName}
            status={status}
            error={error}
            isSample={isSample}
            onFileChange={setFile}
            onUseSample={resetToSample}
          />

          <Card>
            <CardHeader>
              <CardTitle>{t('assemblyViewer.controls.title')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div className="space-y-1">
                  <Label htmlFor="auto-rotate-toggle">
                    {t('assemblyViewer.controls.autoRotate')}
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    {t('assemblyViewer.controls.autoRotateHint')}
                  </p>
                </div>
                <Switch
                  id="auto-rotate-toggle"
                  checked={autoRotate}
                  onCheckedChange={setAutoRotate}
                />
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleResetView}
                className="w-full"
              >
                {t('assemblyViewer.controls.resetView')}
              </Button>
            </CardContent>
          </Card>

          <AssemblyExplorerPanel />
        </aside>

        <section className="relative flex flex-1 min-h-[720px] overflow-hidden rounded-3xl border border-border/60 bg-gradient-to-br from-slate-900/70 via-slate-950/80 to-slate-950/95 shadow-[inset_0_12px_35px_rgba(5,8,15,0.45)]">
          {modelUrl ? (
            <AssemblyCanvas
              modelUrl={modelUrl}
              autoRotate={autoRotate}
              controlsRef={controlsRef}
              onReady={markReady}
            />
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 px-6 text-center">
              <p className="text-sm font-semibold text-foreground/80">
                {t('assemblyViewer.status.idle')}
              </p>
              <p className="text-xs text-muted-foreground">
                {t('assemblyViewer.input.hint')}
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
