import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { Loader, OrbitControls, Environment, AdaptiveDpr, AdaptiveEvents } from '@react-three/drei';
import type { ElementDetails, ElectronShell } from '../../../data/elements';
import { useAtomStore } from '../state/useAtomStore';
import { AtomSystem } from './AtomSystem';
import { SceneBackdrop } from './SceneBackdrop';

interface AtomCanvasProps {
  element: ElementDetails;
  shells: ElectronShell[];
}

export function AtomCanvas({ element, shells }: AtomCanvasProps) {
  const autoRotate = useAtomStore((state) => state.view.autoRotate);
  const freezeMotion = useAtomStore((state) => state.view.freezeMotion);

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
          <AtomSystem element={element} shells={shells} />
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
