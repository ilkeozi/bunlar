import type * as THREE from 'three';
import { extractOcafEntry } from './ocaf';

export function indexMeshesByOcafEntry(
  model: THREE.Object3D
): Map<string, THREE.Mesh[]> {
  const map = new Map<string, THREE.Mesh[]>();

  model.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (mesh?.isMesh !== true) return;

    const entry = extractOcafEntry(mesh.name ?? '');
    if (!entry) return;

    const list = map.get(entry);
    if (list) list.push(mesh);
    else map.set(entry, [mesh]);
  });

  return map;
}
