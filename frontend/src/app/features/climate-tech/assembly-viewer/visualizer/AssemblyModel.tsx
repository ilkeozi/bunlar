import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { centerModel } from './modeling';
import { useAssemblyExplorerStore } from '../state/useAssemblyExplorerStore';
import { extractOcafEntry } from '../utils/ocaf';
import { indexMeshesByOcafEntry } from '../utils/sceneIndex';
import type { ThreeEvent } from '@react-three/fiber';
import { getEffectiveHiddenLeafPartOcafEntries } from '../utils/nodeMapIndex';

const isLight = (object: THREE.Object3D): object is THREE.Light =>
  object instanceof THREE.Light;

type AssemblyModelProps = {
  url: string;
  onReady?: () => void;
};

export function AssemblyModel({ url, onReady }: AssemblyModelProps) {
  const { scene } = useGLTF(url);
  const nodeMap = useAssemblyExplorerStore((state) => state.nodeMap);
  const explicitHiddenNodeIds = useAssemblyExplorerStore(
    (state) => state.explicitHiddenNodeIds
  );
  const meshesByOcafEntryRef = useRef<Map<string, THREE.Mesh[]> | null>(null);

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
    meshesByOcafEntryRef.current = meshesByOcafEntry;
    useAssemblyExplorerStore.getState().setMeshesByOcafEntry(meshesByOcafEntry);

    return () => {
      meshesByOcafEntryRef.current = null;
      useAssemblyExplorerStore.getState().setMeshesByOcafEntry(null);
    };
  }, [model]);

  useEffect(() => {
    const meshesByOcafEntry = meshesByOcafEntryRef.current;
    if (!meshesByOcafEntry) return;

    const hiddenEntries = nodeMap
      ? getEffectiveHiddenLeafPartOcafEntries(nodeMap, explicitHiddenNodeIds)
      : new Set<string>();

    for (const [entry, meshes] of meshesByOcafEntry) {
      const isHidden = hiddenEntries.has(entry);
      for (const mesh of meshes) {
        if (isHidden) {
          if (mesh.userData.__origRaycast === undefined) {
            mesh.userData.__origRaycast = mesh.raycast;
          }
          mesh.visible = false;
          mesh.raycast = () => null;
        } else {
          mesh.visible = true;
          if (mesh.userData.__origRaycast !== undefined) {
            mesh.raycast = mesh.userData.__origRaycast;
            delete mesh.userData.__origRaycast;
          }
        }
      }
    }
  }, [explicitHiddenNodeIds, model, nodeMap]);

  const handlePointerDown = useCallback((event: ThreeEvent<PointerEvent>) => {
    event.stopPropagation();

    const mesh = event.object as THREE.Mesh;
    if (mesh?.isMesh !== true) return;

    // Prefer the hit mesh name, but fall back to named ancestors (some GLBs name the node).
    let entry = extractOcafEntry(mesh.name ?? '');
    if (!entry) {
      let cursor: THREE.Object3D | null = mesh.parent;
      while (cursor && !entry) {
        entry = extractOcafEntry(cursor.name ?? '');
        cursor = cursor.parent;
      }
    }
    if (!entry) return;

    useAssemblyExplorerStore.getState().selectOcafEntry(entry, '3d');
  }, []);

  return <primitive object={model} onPointerDown={handlePointerDown} />;
}
