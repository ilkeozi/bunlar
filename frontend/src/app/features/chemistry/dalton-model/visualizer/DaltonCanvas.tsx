import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { AdaptiveDpr, AdaptiveEvents, Environment, Loader, OrbitControls } from '@react-three/drei';
import type { ElementDetails } from '../../../../data/elements';
import { useDaltonStore } from '../state/useDaltonStore';
import { DaltonSystem } from './DaltonSystem';
import { SceneBackdrop } from './SceneBackdrop';

interface DaltonCanvasProps {
  element: ElementDetails;
}

export function DaltonCanvas({ element }: DaltonCanvasProps) {
  const autoRotate = useDaltonStore((state) => state.view.autoRotate);
  const freezeMotion = useDaltonStore((state) => state.view.freezeMotion);

  return (
    <div className="absolute inset-0">
      <Canvas
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: false }}
        camera={{ position: [0, 6, 14], fov: 42, near: 0.1, far: 120 }}
      >
        <fog attach="fog" args={[0x05070d, 25, 85]} />

        <AdaptiveDpr pixelated={false} />
        <AdaptiveEvents />

        <Suspense fallback={null}>
          <SceneBackdrop />
          <DaltonSystem element={element} />
          <Environment preset="warehouse" background={false} blur={0.6} />
        </Suspense>

        <OrbitControls
          enableDamping
          dampingFactor={0.08}
          minDistance={4}
          maxDistance={50}
          autoRotate={autoRotate && !freezeMotion}
          autoRotateSpeed={0.35}
          enablePan
        />
      </Canvas>
      <Loader dataInterpolation={(ratio) => `${Math.round(ratio * 100)}%`} />
    </div>
  );
}
