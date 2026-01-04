import { useEffect } from 'react';
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
} from '../types';
import { GearboxModel } from './GearboxModel';

interface GearboxCanvasProps {
  explode: number;
  autoRotate: boolean;
  debugMaterials: boolean;
  pcfOverlay: boolean;
  pcfOverlayMode: PcfOverlayMode;
  pcfMaxByMode: Record<PcfOverlayMode, number>;
  controlsRef: RefObject<OrbitControlsImpl | null>;
  onPartsCount?: (count: number) => void;
  onHierarchy?: (items: HierarchyItem[]) => void;
  onPartGroups?: (groups: PartGroup[]) => void;
  onAssemblyGroups?: (groups: AssemblyGroup[]) => void;
}

export function GearboxCanvas({
  explode,
  autoRotate,
  debugMaterials,
  pcfOverlay,
  pcfOverlayMode,
  pcfMaxByMode,
  controlsRef,
  onPartsCount,
  onHierarchy,
  onPartGroups,
  onAssemblyGroups,
}: GearboxCanvasProps) {
  useEffect(() => {
    if (!controlsRef.current) {
      return;
    }

    controlsRef.current.target.set(0, 0, 0);
    controlsRef.current.update();
    controlsRef.current.saveState();
  }, [controlsRef]);

  return (
    <div className="absolute inset-0">
      <Canvas camera={{ position: [5, 5, 5], fov: 40, near: 0.1, far: 500 }}>
        <Environment preset="warehouse" />

        <GearboxModel
          explode={explode}
          debugMaterials={debugMaterials}
          pcfOverlay={pcfOverlay}
          pcfOverlayMode={pcfOverlayMode}
          pcfMaxByMode={pcfMaxByMode}
          onPartsCount={onPartsCount}
          onHierarchy={onHierarchy}
          onPartGroups={onPartGroups}
          onAssemblyGroups={onAssemblyGroups}
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
