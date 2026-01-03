import * as THREE from 'three';
import type { PartMaterialMeta } from '../types';
import { normalizeMatchKey, normalizeMatchKeyLoose, normalizePartName } from './modeling';

type MaterialDefinition = {
  color: string;
  metalness: number;
  roughness: number;
  envMapIntensity?: number;
};

export type MaterialLibrary = Record<string, THREE.MeshStandardMaterial>;
export type DebugMaterialOptions = {
  enabled: boolean;
  material: THREE.MeshStandardMaterial;
  targetMaterialGuess?: string;
};

export const createMaterialLibrary = (
  definitions: Record<string, MaterialDefinition> = {}
) => {
  const build = (
    color: string,
    metalness: number,
    roughness: number,
    envMapIntensity = 1
  ) =>
    new THREE.MeshStandardMaterial({
      color,
      metalness,
      roughness,
      envMapIntensity,
    });
  const library: MaterialLibrary = {};
  Object.entries(definitions).forEach(([key, value]) => {
    library[key] = build(
      value.color,
      value.metalness,
      value.roughness,
      value.envMapIntensity ?? 1
    );
  });
  library.steel_default = build('#656d76', 0.75, 0.5);
  return library;
};

export const createDebugMaterial = () => {
  const material = new THREE.MeshStandardMaterial({
    color: '#ff2b2b',
    metalness: 0.15,
    roughness: 0.35,
    emissive: '#ff2b2b',
    emissiveIntensity: 1.1,
  });
  material.toneMapped = false;
  return material;
};

export const createMaterialIndex = (parts: PartMaterialMeta[] = []) => {
  const index = new Map<string, PartMaterialMeta>();
  const normalizeKey = (value: string) => normalizePartName(value).toLowerCase();
  parts.forEach((part) => {
    if (part.key) {
      index.set(part.key.toLowerCase(), part);
      index.set(normalizeKey(part.key), part);
      index.set(normalizeMatchKey(part.key), part);
      index.set(normalizeMatchKeyLoose(part.key), part);
    }
    if (part.name) {
      index.set(part.name.toLowerCase(), part);
      index.set(normalizeKey(part.name), part);
      index.set(normalizeMatchKey(part.name), part);
      index.set(normalizeMatchKeyLoose(part.name), part);
    }
  });
  return index;
};

export const resolveMaterial = (
  library: MaterialLibrary,
  meta?: PartMaterialMeta,
  debugOptions?: DebugMaterialOptions
) => {
  if (debugOptions?.enabled) {
    if (!debugOptions.targetMaterialGuess) {
      return debugOptions.material;
    }
    if (meta?.material_guess === debugOptions.targetMaterialGuess) {
      return debugOptions.material;
    }
  }
  const guess = meta?.material_guess as keyof MaterialLibrary | undefined;
  if (guess && library[guess]) {
    return library[guess];
  }
  return library.steel_default;
};

export const applyMaterial = (mesh: THREE.Mesh, material: THREE.Material) => {
  if (Array.isArray(mesh.material)) {
    mesh.material = mesh.material.map(() => material);
  } else {
    mesh.material = material;
  }
  const materials = Array.isArray(mesh.material)
    ? mesh.material
    : [mesh.material];
  materials.forEach((mat) => {
    mat.needsUpdate = true;
  });
};
