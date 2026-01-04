import * as THREE from 'three';
import type { PartMaterialMeta, PcfOverlayMode } from '../types';
import { normalizeMatchKey, normalizeMatchKeyLoose, normalizePartName } from './modeling';

type MaterialDefinition = {
  color: string;
  metalness: number;
  roughness: number;
  envMapIntensity?: number;
};

type PcfBreakdown = {
  material?: number;
  manufacturing?: number;
  transport?: number;
};

export type MaterialLibrary = Record<string, THREE.MeshStandardMaterial>;
export type DebugMaterialOptions = {
  enabled: boolean;
  material: THREE.MeshStandardMaterial;
  targetMaterialGuess?: string;
};
export type PcfOverlayOptions = {
  enabled: boolean;
  mode: PcfOverlayMode;
  maxPcf: number;
  cache: Map<string, THREE.MeshStandardMaterial>;
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

const HEATMAP_STOPS = [
  { stop: 0, color: new THREE.Color('#2563eb') },
  { stop: 0.45, color: new THREE.Color('#22c55e') },
  { stop: 0.7, color: new THREE.Color('#f59e0b') },
  { stop: 1, color: new THREE.Color('#ef4444') },
];

const getBreakdown = (meta?: PartMaterialMeta) =>
  (meta?.pcf?.breakdown as PcfBreakdown | undefined) ?? undefined;

const getHeatmapColor = (value: number) => {
  const clamped = Math.min(Math.max(value, 0), 1);
  for (let i = 0; i < HEATMAP_STOPS.length - 1; i += 1) {
    const current = HEATMAP_STOPS[i];
    const next = HEATMAP_STOPS[i + 1];
    if (clamped <= next.stop) {
      const range = next.stop - current.stop || 1;
      const t = (clamped - current.stop) / range;
      return current.color.clone().lerp(next.color, t);
    }
  }
  return HEATMAP_STOPS[HEATMAP_STOPS.length - 1].color.clone();
};

const createPcfOverlayMaterial = (
  breakdown: PcfBreakdown,
  mode: PcfOverlayMode,
  maxPcf: number
) => {
  const materialValue = breakdown.material ?? 0;
  const manufacturingValue = breakdown.manufacturing ?? 0;
  const transportValue = breakdown.transport ?? 0;
  const total = materialValue + manufacturingValue + transportValue;
  if (total <= 0 || maxPcf <= 0) {
    return null;
  }

  const value =
    mode === 'material'
      ? materialValue
      : mode === 'manufacturing'
        ? manufacturingValue
        : mode === 'transport'
          ? transportValue
          : total;

  const intensity = Math.min(value / maxPcf, 1);
  const color = getHeatmapColor(intensity);
  const emissiveIntensity = 0.25 + intensity * 0.6;

  const overlayMaterial = new THREE.MeshStandardMaterial({
    color,
    metalness: 0.15,
    roughness: 0.72,
    emissive: color,
    emissiveIntensity,
  });
  overlayMaterial.toneMapped = false;
  return overlayMaterial;
};

const resolveOverlayMaterial = (
  meta: PartMaterialMeta | undefined,
  options: PcfOverlayOptions
) => {
  if (!options.enabled || !meta) {
    return null;
  }
  const key = meta.id ?? meta.key ?? meta.name;
  if (!key) {
    return null;
  }
  const cacheKey = `${options.mode}:${key}`;
  const cached = options.cache.get(cacheKey);
  if (cached) {
    return cached;
  }
  const breakdown = getBreakdown(meta);
  if (!breakdown) {
    return null;
  }
  const material = createPcfOverlayMaterial(
    breakdown,
    options.mode,
    options.maxPcf
  );
  if (!material) {
    return null;
  }
  options.cache.set(cacheKey, material);
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
  debugOptions?: DebugMaterialOptions,
  overlayOptions?: PcfOverlayOptions
) => {
  if (debugOptions?.enabled) {
    if (!debugOptions.targetMaterialGuess) {
      return debugOptions.material;
    }
    if (meta?.material_guess === debugOptions.targetMaterialGuess) {
      return debugOptions.material;
    }
  }
  if (overlayOptions?.enabled) {
    const overlayMaterial = resolveOverlayMaterial(meta, overlayOptions);
    if (overlayMaterial) {
      return overlayMaterial;
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
