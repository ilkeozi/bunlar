import { useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { ControlsToggle } from '../../../features/climate-tech/carbon-aware-motor-assembly/components/ControlsToggle';
import { ModelMetadataGrid } from '../../../features/climate-tech/carbon-aware-motor-assembly/components/ModelMetadataGrid';
import { OverlayLegend } from '../../../features/climate-tech/carbon-aware-motor-assembly/components/OverlayLegend';
import { TheaterShell } from '../../../features/climate-tech/carbon-aware-motor-assembly/components/TheaterShell';
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
  const [isTheater, setIsTheater] = useState(false);
  const [controlsOpen, setControlsOpen] = useState(false);
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

  if (isTheater) {
    return (
      <TheaterShell
        controlsOpen={controlsOpen}
        onControlsToggle={() => setControlsOpen((open) => !open)}
        onExit={() => setIsTheater(false)}
        overlayLegend={
          <OverlayLegend
            enabled={overlayEnabled}
            overlayModeLabel={overlayModeLabel}
            maxValue={pcfMaxByMode[pcfOverlayMode]}
            mode={pcfOverlayMode}
            className="absolute bottom-6 left-6 z-10 w-56 sm:w-64"
          />
        }
        controls={
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
            isTheater={isTheater}
            onTheaterChange={setIsTheater}
          />
        }
      >
        {(tooltipAvoidRect) => (
          <GearboxCanvas
            explode={explode}
            autoRotate={autoRotate}
            debugMaterials={debugMaterials}
            pcfOverlayMode={pcfOverlayMode}
            pcfMaxByMode={pcfMaxByMode}
            tooltipAvoidRect={tooltipAvoidRect}
            controlsRef={controlsRef}
            onPartsCount={setPartsCount}
            onHierarchy={setHierarchy}
            onPartGroups={setPartGroups}
            onAssemblyGroups={setAssemblyGroups}
          />
        )}
      </TheaterShell>
    );
  }

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
        <div className="flex items-center justify-between xl:hidden">
          <ControlsToggle
            controlsOpen={controlsOpen}
            onToggle={() => setControlsOpen((open) => !open)}
          />
        </div>
        <aside
          className={`flex w-full flex-shrink-0 flex-col gap-6 xl:max-w-sm ${
            controlsOpen ? 'flex' : 'hidden'
          } xl:flex`}
        >
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
            isTheater={isTheater}
            onTheaterChange={setIsTheater}
          />
        </aside>
        <section className="relative flex flex-1 min-h-[720px] overflow-hidden rounded-3xl border border-border/60 bg-gradient-to-br from-slate-900/70 via-slate-950/80 to-slate-950/95 shadow-[inset_0_12px_35px_rgba(5,8,15,0.45)]">
          <OverlayLegend
            enabled={overlayEnabled}
            overlayModeLabel={overlayModeLabel}
            maxValue={pcfMaxByMode[pcfOverlayMode]}
            mode={pcfOverlayMode}
            className="absolute bottom-4 left-4 z-10 w-56 sm:w-64"
          />
          <GearboxCanvas
            explode={explode}
            autoRotate={autoRotate}
            debugMaterials={debugMaterials}
            pcfOverlayMode={pcfOverlayMode}
            pcfMaxByMode={pcfMaxByMode}
            tooltipAvoidRect={null}
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
