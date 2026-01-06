import { useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { ModelMetadataGrid } from '../../../features/climate-tech/carbon-aware-motor-assembly/components/ModelMetadataGrid';
import { ViewControls } from '../../../features/climate-tech/carbon-aware-motor-assembly/components/ViewControls';
import type {
  AssemblyGroup,
  HierarchyItem,
  PartGroup,
  PcfOverlayMode,
} from '../../../features/climate-tech/carbon-aware-motor-assembly/types';
import { GearboxCanvas } from '../../../features/climate-tech/carbon-aware-motor-assembly/visualizer/GearboxCanvas';
import partsCatalog from '../../../data/climate-tech/partsCatalog.json';
import { useTranslation } from '../../../i18n/useTranslation';

export function CarbonAwareMotorAssemblyPage() {
  const { t } = useTranslation();
  const controlsRef = useRef<OrbitControlsImpl | null>(null);
  const [autoRotate, setAutoRotate] = useState(false);
  const [debugMaterials, setDebugMaterials] = useState(false);
  const [pcfOverlayMode, setPcfOverlayMode] =
    useState<PcfOverlayMode>('none');
  const [explode, setExplode] = useState(0);
  const [partsCount, setPartsCount] = useState<number | null>(null);
  const [hierarchy, setHierarchy] = useState<HierarchyItem[]>([]);
  const [partGroups, setPartGroups] = useState<PartGroup[]>([]);
  const [assemblyGroups, setAssemblyGroups] = useState<AssemblyGroup[]>([]);
  const pcfMaxByMode = useMemo(() => {
    const max: Record<PcfOverlayMode, number> = {
      none: 0,
      total: 0,
      material: 0,
      manufacturing: 0,
      transport: 0,
    };
    (partsCatalog.parts ?? []).forEach((part) => {
      const breakdown = part?.pcf?.breakdown;
      const material = breakdown?.material ?? 0;
      const manufacturing = breakdown?.manufacturing ?? 0;
      const transport = breakdown?.transport ?? 0;
      const total = material + manufacturing + transport;
      max.total = Math.max(max.total, total);
      max.material = Math.max(max.material, material);
      max.manufacturing = Math.max(max.manufacturing, manufacturing);
      max.transport = Math.max(max.transport, transport);
    });
    return max;
  }, []);
  const overlayEnabled = pcfOverlayMode !== 'none';
  const overlayModeLabel = (() => {
    switch (pcfOverlayMode) {
      case 'none':
        return t('controls.pcfOverlayNone');
      case 'total':
        return t('controls.pcfOverlayTotal');
      case 'material':
        return t('controls.pcfOverlayMaterial');
      case 'manufacturing':
        return t('controls.pcfOverlayManufacturing');
      case 'transport':
        return t('controls.pcfOverlayTransport');
      default:
        return pcfOverlayMode;
    }
  })();

  const handleResetView = () => {
    controlsRef.current?.reset();
    controlsRef.current?.update();
  };

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <Link
          to="/subjects/climate-tech"
          className="text-xs font-semibold uppercase tracking-wide text-primary/80"
        >
          ← {t('subjects.climateTech.title')}
        </Link>
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          {t('climateTech.modules.carbonAware.title')}
        </h2>
        <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
          {t('climateTech.modules.carbonAware.description')}
        </p>
      </header>

      <div className="flex flex-1 flex-col gap-7 xl:flex-row">
        <aside className="flex w-full flex-shrink-0 flex-col gap-6 xl:max-w-sm">
          <ViewControls
            autoRotate={autoRotate}
            onAutoRotateChange={setAutoRotate}
            debugMaterials={debugMaterials}
            onDebugMaterialsChange={setDebugMaterials}
            pcfOverlayMode={pcfOverlayMode}
            onPcfOverlayModeChange={setPcfOverlayMode}
            explode={explode}
            onExplodeChange={setExplode}
            partsCount={partsCount}
            onResetView={handleResetView}
          />
        </aside>
        <section className="relative flex flex-1 min-h-[720px] overflow-hidden rounded-3xl border border-border/60 bg-gradient-to-br from-slate-900/70 via-slate-950/80 to-slate-950/95 shadow-[inset_0_12px_35px_rgba(5,8,15,0.45)]">
          {overlayEnabled && (
            <div className="pointer-events-none absolute bottom-4 left-4 z-10 w-56 rounded-xl border border-border/50 bg-slate-950/60 p-3 text-xs text-muted-foreground shadow-lg backdrop-blur sm:w-64">
              <div>
                {t('controls.pcfOverlayMode')}: {overlayModeLabel} (
                {t('controls.pcfLegendUnit')})
              </div>
              <div className="mt-2 flex items-center justify-between text-[11px]">
                <span>{t('controls.pcfLegendLow')}</span>
                <span>
                  {t('controls.pcfLegendHigh')} {pcfMaxByMode[pcfOverlayMode].toFixed(2)}
                </span>
              </div>
              <div
                className="mt-2 h-2 w-full rounded-full"
                style={{
                  background:
                    'linear-gradient(90deg, #2563eb 0%, #22c55e 45%, #f59e0b 70%, #ef4444 100%)',
                }}
              />
            </div>
          )}
          <GearboxCanvas
            explode={explode}
            autoRotate={autoRotate}
            debugMaterials={debugMaterials}
            pcfOverlayMode={pcfOverlayMode}
            pcfMaxByMode={pcfMaxByMode}
            controlsRef={controlsRef}
            onPartsCount={setPartsCount}
            onHierarchy={setHierarchy}
            onPartGroups={setPartGroups}
            onAssemblyGroups={setAssemblyGroups}
          />
        </section>
      </div>

      <ModelMetadataGrid
        hierarchy={hierarchy}
        partGroups={partGroups}
        assemblyGroups={assemblyGroups}
      />
    </div>
  );
}
