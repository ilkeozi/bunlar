import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { ModelMetadataGrid } from '../../../features/climate-tech/carbon-aware-motor-assembly/components/ModelMetadataGrid';
import { ViewControls } from '../../../features/climate-tech/carbon-aware-motor-assembly/components/ViewControls';
import type {
  AssemblyGroup,
  HierarchyItem,
  PartGroup,
} from '../../../features/climate-tech/carbon-aware-motor-assembly/types';
import { GearboxCanvas } from '../../../features/climate-tech/carbon-aware-motor-assembly/visualizer/GearboxCanvas';
import { useTranslation } from '../../../i18n/useTranslation';

export function CarbonAwareMotorAssemblyPage() {
  const { t } = useTranslation();
  const controlsRef = useRef<OrbitControlsImpl | null>(null);
  const [autoRotate, setAutoRotate] = useState(false);
  const [debugMaterials, setDebugMaterials] = useState(false);
  const [explode, setExplode] = useState(0);
  const [partsCount, setPartsCount] = useState<number | null>(null);
  const [hierarchy, setHierarchy] = useState<HierarchyItem[]>([]);
  const [partGroups, setPartGroups] = useState<PartGroup[]>([]);
  const [assemblyGroups, setAssemblyGroups] = useState<AssemblyGroup[]>([]);

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
          <Card>
            <CardHeader>
              <CardTitle>{t('climateTech.modules.carbonAware.title')}</CardTitle>
              <CardDescription>
                {t('climateTech.modules.carbonAware.description')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {t('climateTech.modules.carbonAware.placeholder')}
              </p>
            </CardContent>
          </Card>
          <ViewControls
            autoRotate={autoRotate}
            onAutoRotateChange={setAutoRotate}
            debugMaterials={debugMaterials}
            onDebugMaterialsChange={setDebugMaterials}
            explode={explode}
            onExplodeChange={setExplode}
            partsCount={partsCount}
            onResetView={handleResetView}
          />
        </aside>
        <section className="relative flex flex-1 min-h-[540px] overflow-hidden rounded-3xl border border-border/60 bg-gradient-to-br from-slate-900/70 via-slate-950/80 to-slate-950/95 shadow-[inset_0_12px_35px_rgba(5,8,15,0.45)]">
          <GearboxCanvas
            explode={explode}
            autoRotate={autoRotate}
            debugMaterials={debugMaterials}
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
