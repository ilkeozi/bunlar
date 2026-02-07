import { useCallback, useEffect, useMemo } from 'react';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { centerModel } from './modeling';
import { useAssemblyExplorerStore } from '../state/useAssemblyExplorerStore';
import { extractOcafEntry } from '../utils/ocaf';
import { indexMeshesByOcafEntry } from '../utils/sceneIndex';
import { SelectionOutline } from './SelectionOutline';
import type { ThreeEvent } from '@react-three/fiber';

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

  useEffect(() => {
    const meshesByOcafEntry = indexMeshesByOcafEntry(model);
    useAssemblyExplorerStore.getState().setMeshesByOcafEntry(meshesByOcafEntry);

    return () => {
      useAssemblyExplorerStore.getState().setMeshesByOcafEntry(null);
    };
  }, [model]);

  const handlePointerDown = useCallback((event: ThreeEvent<PointerEvent>) => {
    event.stopPropagation();

    const mesh = event.object as THREE.Mesh;
    if (mesh?.isMesh !== true) return;

    const entry = extractOcafEntry(mesh.name ?? '');
    if (!entry) return;

    useAssemblyExplorerStore.getState().selectOcafEntry(entry, '3d');
  }, []);

  return (
    <>
      <primitive object={model} onPointerDown={handlePointerDown} />
      <SelectionOutline />
    </>
  );
}
