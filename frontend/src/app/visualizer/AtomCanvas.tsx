import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { Loader, OrbitControls, Environment, AdaptiveDpr, AdaptiveEvents } from '@react-three/drei';
import type { ElementDetails, ElectronShell } from '../data/elements';
import { useAtomStore } from '../state/useAtomStore';
import { AtomSystem } from './AtomSystem';
import { SceneBackdrop } from './SceneBackdrop';

interface AtomCanvasProps {
  element: ElementDetails;
  shells: ElectronShell[];
}

export function AtomCanvas({ element, shells }: AtomCanvasProps) {
  const autoRotate = useAtomStore((state) => state.view.autoRotate);

  return (
    <div className="atom-viewer">
      <Canvas
        shadows
        gl={{ antialias: true, alpha: false }}
        camera={{ position: [0, 6, 14], fov: 42, near: 0.1, far: 120 }}
      >
        <fog attach="fog" args={[0x05070d, 25, 85]} />

        <AdaptiveDpr pixelated={false} />
        <AdaptiveEvents />

        <Suspense fallback={null}>
          <SceneBackdrop />
          <AtomSystem element={element} shells={shells} />
          <Environment preset="warehouse" background={false} blur={0.6} />
        </Suspense>

        <OrbitControls
          enableDamping
          dampingFactor={0.08}
          minDistance={4}
          maxDistance={50}
          autoRotate={autoRotate}
          autoRotateSpeed={0.35}
          enablePan={false}
        />
      </Canvas>
      <Loader dataInterpolation={(ratio) => `${Math.round(ratio * 100)}%`} />
    </div>
  );
}
