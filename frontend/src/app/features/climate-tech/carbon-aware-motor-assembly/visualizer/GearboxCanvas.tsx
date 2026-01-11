import { useCallback, useEffect, useState } from 'react';
import type { RefObject } from 'react';
import { Canvas } from '@react-three/fiber';
import {
  Environment,
  GizmoHelper,
  GizmoViewport,
  Loader,
  OrbitControls,
} from '@react-three/drei';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import type {
  AssemblyGroup,
  HierarchyItem,
  PartGroup,
  PcfOverlayMode,
  SelectedPart,
} from '../types';
import { PartTooltip } from '../components/PartTooltip';
import { GearboxModel } from './GearboxModel';

interface GearboxCanvasProps {
  explode: number;
  autoRotate: boolean;
  debugMaterials: boolean;
  pcfOverlayMode: PcfOverlayMode;
  pcfMaxByMode: Record<PcfOverlayMode, number>;
  controlsRef: RefObject<OrbitControlsImpl | null>;
  tooltipAvoidRect?: {
    left: number;
    right: number;
    top: number;
    bottom: number;
  } | null;
  onPartsCount?: (count: number) => void;
  onHierarchy?: (items: HierarchyItem[]) => void;
  onPartGroups?: (groups: PartGroup[]) => void;
  onAssemblyGroups?: (groups: AssemblyGroup[]) => void;
}

export function GearboxCanvas({
  explode,
  autoRotate,
  debugMaterials,
  pcfOverlayMode,
  pcfMaxByMode,
  controlsRef,
  tooltipAvoidRect,
  onPartsCount,
  onHierarchy,
  onPartGroups,
  onAssemblyGroups,
}: GearboxCanvasProps) {
  const [selectedPart, setSelectedPart] = useState<SelectedPart | null>(null);
  useEffect(() => {
    if (!controlsRef.current) {
      return;
    }

    controlsRef.current.target.set(0, 0, 0);
    controlsRef.current.update();
    controlsRef.current.saveState();
  }, [controlsRef]);

  const handlePointerMissed = useCallback(() => {
    setSelectedPart(null);
  }, []);

  return (
    <div className="absolute inset-0">
      <Canvas
        camera={{ position: [5, 5, 5], fov: 40, near: 0.1, far: 500 }}
        onPointerMissed={handlePointerMissed}
      >
        <Environment preset="warehouse" />

        <GearboxModel
          explode={explode}
          debugMaterials={debugMaterials}
          pcfOverlayMode={pcfOverlayMode}
          pcfMaxByMode={pcfMaxByMode}
          selectedMesh={selectedPart?.mesh ?? null}
          onPartSelect={(selection) =>
            setSelectedPart((prev) =>
              prev?.mesh === selection?.mesh ? prev : selection
            )
          }
          onPartsCount={onPartsCount}
          onHierarchy={onHierarchy}
          onPartGroups={onPartGroups}
          onAssemblyGroups={onAssemblyGroups}
        />
        <PartTooltip
          selection={selectedPart}
          showEmissions={pcfOverlayMode !== 'none'}
          avoidRect={tooltipAvoidRect ?? null}
        />
        <GizmoHelper alignment="bottom-right" margin={[80, 80]}>
          <GizmoViewport
            axisColors={['#ff7a8a', '#6cb6ff', '#7be3b7']}
            labelColor="white"
          />
        </GizmoHelper>

        <OrbitControls ref={controlsRef} autoRotate={autoRotate} />
      </Canvas>
      <Loader dataInterpolation={(ratio) => `${Math.round(ratio * 100)}%`} />
    </div>
  );
}
