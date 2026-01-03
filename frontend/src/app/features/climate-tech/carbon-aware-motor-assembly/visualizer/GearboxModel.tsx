import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import partsCatalog from '../../../../data/climate-tech/partsCatalog.json';
import type { AssemblyGroup, HierarchyItem, PartGroup } from '../types';
import {
  applyMaterial,
  createDebugMaterial,
  createMaterialIndex,
  createMaterialLibrary,
  resolveMaterial,
} from './materials';
import {
  buildExplodeParts,
  collectAssemblyGroups,
  collectHierarchy,
  collectPartGroups,
  normalizeMatchKey,
  normalizeMatchKeyLoose,
  normalizePartName,
  type ExplodePart,
} from './modeling';

const GEARBOX_MODEL_URL = '/models/blender.glb';
const DEBUG_MATERIAL_GUESS = 'steel_fastener_12_9';

export function GearboxModel({
  explode,
  debugMaterials,
  onPartsCount,
  onHierarchy,
  onPartGroups,
  onAssemblyGroups,
}: {
  explode: number;
  debugMaterials: boolean;
  onPartsCount?: (count: number) => void;
  onHierarchy?: (items: HierarchyItem[]) => void;
  onPartGroups?: (groups: PartGroup[]) => void;
  onAssemblyGroups?: (groups: AssemblyGroup[]) => void;
}) {
  const { scene } = useGLTF(GEARBOX_MODEL_URL);
  const isMesh = useCallback(
    (object: THREE.Object3D): object is THREE.Mesh =>
      (object as THREE.Mesh).isMesh === true,
    []
  );
  const isLight = useCallback(
    (object: THREE.Object3D): object is THREE.Light =>
      (object as THREE.Light).isLight === true,
    []
  );
  const materialLibrary = useMemo(
    () =>
      createMaterialLibrary(
        (partsCatalog.materials as Record<
          string,
          {
            color: string;
            metalness: number;
            roughness: number;
            envMapIntensity?: number;
          }
        >) ?? {}
      ),
    []
  );
  const materialIndex = useMemo(
    () => createMaterialIndex(partsCatalog.parts ?? []),
    []
  );
  const debugMaterial = useMemo(() => createDebugMaterial(), []);
  const hasLoggedUnmatched = useRef(false);
  const model = useMemo(() => {
    const cloned = scene.clone(true);
    const lights: THREE.Light[] = [];
    cloned.traverse((child) => {
      if (isLight(child)) {
        lights.push(child);
      }
    });
    lights.forEach((light) => light.parent?.remove(light));

    const box = new THREE.Box3().setFromObject(cloned);
    const center = box.getCenter(new THREE.Vector3());
    cloned.position.sub(center);
    cloned.rotation.z = Math.PI / 2;
    cloned.updateMatrixWorld(true);

    return cloned;
  }, [isLight, scene]);

  useEffect(() => {
    const unmatched = new Set<string>();
    model.traverse((child) => {
      if (!isMesh(child)) {
        return;
      }
      const rawName = child.name?.trim() ?? '';
      const normalized = normalizePartName(rawName);
      const matchKey = normalizeMatchKey(rawName);
      const looseKey = normalizeMatchKeyLoose(rawName);
      const meta =
        materialIndex.get(normalized.toLowerCase()) ??
        materialIndex.get(rawName.toLowerCase()) ??
        materialIndex.get(matchKey) ??
        materialIndex.get(looseKey);
      if (!meta && rawName) {
        unmatched.add(rawName);
      }
      applyMaterial(
        child,
        resolveMaterial(materialLibrary, meta, {
          enabled: debugMaterials,
          material: debugMaterial,
          targetMaterialGuess: DEBUG_MATERIAL_GUESS,
        })
      );
    });
    if (
      !hasLoggedUnmatched.current &&
      unmatched.size > 0 &&
      import.meta.env.DEV
    ) {
      hasLoggedUnmatched.current = true;
      console.warn(
        `[GearboxModel] Unmatched mesh names (${unmatched.size}):`,
        Array.from(unmatched).sort()
      );
    }
  }, [
    applyMaterial,
    debugMaterial,
    debugMaterials,
    hasLoggedUnmatched,
    isMesh,
    materialIndex,
    materialLibrary,
    model,
    normalizePartName,
    resolveMaterial,
  ]);

  const parts: ExplodePart[] = useMemo(
    () => buildExplodeParts(model, isMesh),
    [isMesh, model]
  );
  const hierarchy = useMemo(() => collectHierarchy(model), [model]);
  const partGroups = useMemo(
    () => collectPartGroups(model, isMesh),
    [isMesh, model]
  );
  const assemblyGroups = useMemo(
    () => collectAssemblyGroups(model, isMesh),
    [isMesh, model]
  );

  useEffect(() => {
    onPartsCount?.(parts.length);
    onHierarchy?.(hierarchy);
    onPartGroups?.(partGroups);
    onAssemblyGroups?.(assemblyGroups);
  }, [
    onAssemblyGroups,
    onHierarchy,
    onPartGroups,
    onPartsCount,
    assemblyGroups,
    hierarchy,
    partGroups,
    parts.length,
  ]);

  useFrame(() => {
    const distance = explode * 2;
    parts.forEach(({ object, base, dir, magnitude }) => {
      object.position.copy(base).addScaledVector(dir, distance * magnitude);
    });
  });

  return <primitive object={model} />;
}

useGLTF.preload(GEARBOX_MODEL_URL);
