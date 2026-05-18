import * as THREE from 'three';
import type { AssemblyGroup, HierarchyItem, PartGroup } from '../types';

export type ExplodePart = {
  object: THREE.Mesh;
  base: THREE.Vector3;
  dir: THREE.Vector3;
  magnitude: number;
};

export const normalizePartName = (rawName: string) => {
  return rawName
    .replace(/_/g, ' ')
    .replace(/\s*-\s*/g, ' - ')
    .replace(/\s*,\s*/g, ', ')
    .replace(/\s+/g, ' ')
    .trim();
};

export const normalizeMatchKey = (rawName: string) => {
  return normalizePartName(rawName)
    .replace(/(?:\s-\s){2,}/g, ' - ')
    .replace(/[.,]/g, '')
    .replace(/\s+/g, ' ')
    .replace(/(?:\s-\s)+$/g, '')
    .replace(/[\s-]+$/g, '')
    .trim()
    .toLowerCase();
};

export const normalizeMatchKeyLoose = (rawName: string) => {
  return normalizeMatchKey(rawName)
    .replace(/\d+$/, '')
    .replace(/(?:\s-\s)+$/g, '')
    .replace(/[\s-]+$/g, '')
    .trim();
};

const getNodePath = (model: THREE.Object3D, node: THREE.Object3D) => {
  const names: string[] = [];
  let parent = node.parent;
  while (parent && parent !== model) {
    if (parent.name?.trim()) {
      names.unshift(parent.name.trim());
    }
    parent = parent.parent;
  }
  const rootName = model.name?.trim() || 'Model';
  return names.length > 0 ? `${rootName} / ${names.join(' / ')}` : rootName;
};

export const collectHierarchy = (model: THREE.Object3D) => {
  const items: HierarchyItem[] = [];
  let unnamedIndex = 1;
  const rootName = model.name?.trim() || 'Model';
  items.push({ name: rootName, depth: 0, type: model.type });

  model.traverse((child) => {
    if (child === model) {
      return;
    }

    let depth = 0;
    let parent = child.parent;
    while (parent) {
      depth += 1;
      if (parent === model) {
        break;
      }
      parent = parent.parent;
    }

    let name = child.name?.trim();
    if (!name) {
      name = `${child.type} ${unnamedIndex}`;
      unnamedIndex += 1;
    }

    items.push({ name, depth, type: child.type });
  });

  return items;
};

export const collectAssemblyGroups = (
  model: THREE.Object3D,
  isMesh: (object: THREE.Object3D) => object is THREE.Mesh,
) => {
  const assemblyMap = new Map<string, AssemblyGroup>();

  model.traverse((node) => {
    if (node.type === 'Mesh') {
      return;
    }
    const name = node.name?.trim();
    if (!name) {
      return;
    }
    let meshCount = 0;
    node.traverse((child) => {
      if (isMesh(child)) {
        meshCount += 1;
      }
    });
    if (meshCount === 0) {
      return;
    }
    const path = getNodePath(model, node);
    const key = `${path}/${name}`;
    assemblyMap.set(key, { name, path, meshCount });
  });

  return Array.from(assemblyMap.values()).sort(
    (a, b) => b.meshCount - a.meshCount,
  );
};

export const collectPartGroups = (
  model: THREE.Object3D,
  isMesh: (object: THREE.Object3D) => object is THREE.Mesh,
) => {
  const partMap = new Map<
    string,
    { key: string; name: string; count: number; assemblies: Map<string, number> }
  >();
  let unnamedIndex = 1;

  model.traverse((child) => {
    if (!isMesh(child)) {
      return;
    }
    const rawName = child.name?.trim() || `Mesh ${unnamedIndex++}`;
    const normalized = normalizePartName(rawName);
    const groupKey = normalized || rawName;
    const entry = partMap.get(groupKey) ?? {
      key: groupKey,
      name: normalized || rawName,
      count: 0,
      assemblies: new Map<string, number>(),
    };
    entry.count += 1;
    const assemblyPath = getNodePath(model, child);
    entry.assemblies.set(
      assemblyPath,
      (entry.assemblies.get(assemblyPath) ?? 0) + 1,
    );
    partMap.set(groupKey, entry);
  });

  return Array.from(partMap.values())
    .map((group) => ({
      key: group.key,
      name: group.name,
      count: group.count,
      assemblies: Array.from(group.assemblies.entries())
        .map(([name, count]) => ({ name, count }))
        .sort((a, b) => b.count - a.count),
    }))
    .sort((a, b) => b.count - a.count);
};

export const buildExplodeParts = (
  model: THREE.Object3D,
  isMesh: (object: THREE.Object3D) => object is THREE.Mesh,
) => {
  model.updateMatrixWorld(true);
  const bounds = new THREE.Box3().setFromObject(model);
  const center = bounds.getCenter(new THREE.Vector3());
  const maxAbsX = Math.max(
    Math.abs(bounds.min.x - center.x),
    Math.abs(bounds.max.x - center.x),
  );
  const items: ExplodePart[] = [];

  model.traverse((child) => {
    if (!isMesh(child)) {
      return;
    }

    const base = child.position.clone();
    const worldCenter = new THREE.Vector3();
    const geometry = child.geometry;
    if ('computeBoundingBox' in geometry) {
      geometry.computeBoundingBox();
      geometry.boundingBox?.getCenter(worldCenter);
      worldCenter.applyMatrix4(child.matrixWorld);
    } else {
      child.getWorldPosition(worldCenter);
    }

    const deltaX = worldCenter.x - center.x;
    const sign = deltaX === 0 ? 1 : Math.sign(deltaX);
    const magnitude = maxAbsX > 0 ? Math.max(0.15, Math.abs(deltaX) / maxAbsX) : 1;
    const dirWorld = new THREE.Vector3(sign, 0, 0);
    const parent = child.parent ?? model;
    const dirLocal = dirWorld
      .clone()
      .transformDirection(parent.matrixWorld.clone().invert());
    items.push({ object: child, base, dir: dirLocal, magnitude });
  });

  return items;
};
