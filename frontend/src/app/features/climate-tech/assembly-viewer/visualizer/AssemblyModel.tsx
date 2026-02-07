import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { centerModel } from './modeling';
import { useAssemblyExplorerStore } from '../state/useAssemblyExplorerStore';
import { extractOcafEntry } from '../utils/ocaf';
import { indexMeshesByOcafEntry } from '../utils/sceneIndex';
import type { ThreeEvent } from '@react-three/fiber';
import { getEffectiveHiddenLeafPartOcafEntries } from '../utils/nodeMapIndex';
import { buildOcafEntryByGltfNodeIndex } from '../utils/glb';

const isLight = (object: THREE.Object3D): object is THREE.Light =>
  object instanceof THREE.Light;

type AssemblyModelProps = {
  url: string;
  onReady?: () => void;
};

export function AssemblyModel({ url, onReady }: AssemblyModelProps) {
  const gltf = useGLTF(url) as any;
  const scene = gltf.scene as THREE.Group;
  const parser = gltf.parser as any;
  const nodeMap = useAssemblyExplorerStore((state) => state.nodeMap);
  const explicitHiddenNodeIds = useAssemblyExplorerStore(
    (state) => state.explicitHiddenNodeIds
  );
  const meshesByOcafEntryRef = useRef<Map<string, THREE.Mesh[]> | null>(null);
  const ocafEntryByGltfNodeIndexRef = useRef<Map<number, string>>(new Map());

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

  const resolveOcafEntryForObject = useCallback(
    (obj: THREE.Object3D | null) => {
      // Prefer a mapping derived from glTF node indices (via GLTFLoader parser associations)
      // because Object3D names are not guaranteed to carry the OCAF entry.
      const ocafByIndex = ocafEntryByGltfNodeIndexRef.current;
      if (ocafByIndex.size > 0 && parser?.associations) {
        let cursor: THREE.Object3D | null = obj;
        while (cursor) {
          const assoc = parser.associations.get(cursor);
          const nodeIndex = assoc?.nodes;
          if (typeof nodeIndex === 'number') {
            const entry = ocafByIndex.get(nodeIndex);
            if (entry) return entry;
          }
          cursor = cursor.parent;
        }
      }

      // Fallback: try extracting from names (mesh or ancestor nodes).
      let cursor: THREE.Object3D | null = obj;
      while (cursor) {
        const entry = extractOcafEntry(cursor.name ?? '');
        if (entry) return entry;
        cursor = cursor.parent;
      }
      return null;
    },
    [parser]
  );

  useEffect(() => {
    let cancelled = false;

    async function loadMappingAndIndex() {
      try {
        const res = await fetch(url);
        const buf = await res.arrayBuffer();
        if (cancelled) return;

        ocafEntryByGltfNodeIndexRef.current = buildOcafEntryByGltfNodeIndex(
          new Uint8Array(buf)
        );

        if (
          import.meta.env.DEV &&
          ocafEntryByGltfNodeIndexRef.current.size === 0
        ) {
          console.warn(
            '[assembly-viewer] No OCAF entries found in GLB node names; 3D selection sync may not work.'
          );
        }

        const meshesByOcafEntry = indexMeshesByOcafEntry(
          model,
          resolveOcafEntryForObject
        );
        meshesByOcafEntryRef.current = meshesByOcafEntry;
        useAssemblyExplorerStore
          .getState()
          .setMeshesByOcafEntry(meshesByOcafEntry);
      } catch (err) {
        if (import.meta.env.DEV) {
          console.warn('[assembly-viewer] failed to build OCAF mapping', err);
        }
        meshesByOcafEntryRef.current = new Map();
        useAssemblyExplorerStore.getState().setMeshesByOcafEntry(new Map());
      }
    }

    loadMappingAndIndex();

    return () => {
      cancelled = true;
      meshesByOcafEntryRef.current = null;
      ocafEntryByGltfNodeIndexRef.current = new Map();
      useAssemblyExplorerStore.getState().setMeshesByOcafEntry(null);
    };
  }, [model, resolveOcafEntryForObject, url]);

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

  const handlePointerDown = useCallback(
    (event: ThreeEvent<PointerEvent>) => {
      event.stopPropagation();

      const mesh = event.object as THREE.Mesh;
      if (mesh?.isMesh !== true) return;

      const entry = resolveOcafEntryForObject(mesh);
      if (!entry) return;

      useAssemblyExplorerStore.getState().selectOcafEntry(entry, '3d');
    },
    [resolveOcafEntryForObject]
  );

  return <primitive object={model} onPointerDown={handlePointerDown} />;
}
