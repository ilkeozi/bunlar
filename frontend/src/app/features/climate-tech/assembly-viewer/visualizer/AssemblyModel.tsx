import { useEffect, useMemo } from 'react';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { centerModel } from './modeling';

const isLight = (object: THREE.Object3D): object is THREE.Light =>
  object instanceof THREE.Light;

type AssemblyModelProps = {
  url: string;
  onReady?: () => void;
};

export function AssemblyModel({ url, onReady }: AssemblyModelProps) {
  const { scene } = useGLTF(url);

  const model = useMemo(() => {
    const cloned = scene.clone(true);
    const lights: THREE.Light[] = [];
    cloned.traverse((child) => {
      if (isLight(child)) {
        lights.push(child);
      }
    });
    lights.forEach((light) => light.parent?.remove(light));

    return centerModel(cloned);
  }, [scene]);

  useEffect(() => {
    onReady?.();
  }, [model, onReady]);

  return <primitive object={model} />;
}
