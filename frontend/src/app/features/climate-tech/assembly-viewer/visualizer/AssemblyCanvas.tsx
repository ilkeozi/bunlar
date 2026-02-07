import { Suspense, useEffect } from 'react';
import type { RefObject } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import {
  Environment,
  GizmoHelper,
  GizmoViewport,
  Loader,
  OrbitControls,
} from '@react-three/drei';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { AssemblyModel } from './AssemblyModel';
import { DevPerfOverlay } from '../components/DevPerfOverlay';

interface AssemblyCanvasProps {
  modelUrl: string;
  autoRotate: boolean;
  controlsRef: RefObject<OrbitControlsImpl | null>;
  onReady?: () => void;
}

function CameraRig({
  controlsRef,
}: {
  controlsRef: RefObject<OrbitControlsImpl | null>;
}) {
  const { camera } = useThree();

  useEffect(() => {
    camera.position.set(2.1, 2.1, 2.1);
    camera.updateProjectionMatrix();

    if (controlsRef.current) {
      controlsRef.current.target.set(0, 0, 0);
      controlsRef.current.update();
      controlsRef.current.saveState();
    }
  }, [camera, controlsRef]);

  return null;
}

export function AssemblyCanvas({
  modelUrl,
  autoRotate,
  controlsRef,
  onReady,
}: AssemblyCanvasProps) {
  useEffect(() => {
    if (!controlsRef.current) {
      return;
    }

    controlsRef.current.target.set(0, 0, 0);
    controlsRef.current.update();
    controlsRef.current.saveState();
  }, [controlsRef, modelUrl]);

  return (
    <div className="absolute inset-0">
      <Canvas
        camera={{ position: [2.1, 2.1, 2.1], fov: 40, near: 0.1, far: 500 }}
        dpr={[1, 1]}
        gl={{ antialias: false, powerPreference: 'high-performance' }}
      >
        <Environment preset="warehouse" />

        {import.meta.env.DEV ? <DevPerfOverlay /> : null}

        <Suspense fallback={null}>
          <AssemblyModel key={modelUrl} url={modelUrl} onReady={onReady} />
        </Suspense>

        <CameraRig controlsRef={controlsRef} />

        <GizmoHelper alignment="bottom-right" margin={[80, 80]}>
          <GizmoViewport
            axisColors={['#ff7a8a', '#6cb6ff', '#7be3b7']}
            labelColor="white"
          />
        </GizmoHelper>

        <OrbitControls ref={controlsRef} autoRotate={autoRotate} />
      </Canvas>
      <Loader
        dataInterpolation={(ratio) => {
          const percent = ratio > 1 ? ratio : ratio * 100;
          return `${Math.min(100, Math.round(percent))}%`;
        }}
      />
    </div>
  );
}
