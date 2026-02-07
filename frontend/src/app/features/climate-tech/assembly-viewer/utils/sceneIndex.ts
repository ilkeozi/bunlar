import type * as THREE from 'three';
import { extractOcafEntry } from './ocaf';

function extractOcafEntryFromObject(obj: THREE.Object3D | null): string | null {
  let cursor: THREE.Object3D | null = obj;
  while (cursor) {
    const fromUserData = (cursor.userData as any)?.__ocafEntry;
    if (typeof fromUserData === 'string' && fromUserData.length > 0)
      return fromUserData;

    const entry = extractOcafEntry(cursor.name ?? '');
    if (entry) return entry;
    cursor = cursor.parent;
  }
  return null;
}

export type OcafEntryResolver = (obj: THREE.Object3D | null) => string | null;

export function indexMeshesByOcafEntry(
  model: THREE.Object3D,
  resolveOcafEntry: OcafEntryResolver = extractOcafEntryFromObject
): Map<string, THREE.Mesh[]> {
  const map = new Map<string, THREE.Mesh[]>();

  model.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (mesh?.isMesh !== true) return;

    // Some GLB loaders attach the OCAF-bearing name on an ancestor node rather than
    // the Mesh object itself. Index by the closest ancestor that carries the entry.
    const entry = resolveOcafEntry(mesh);
    if (!entry) return;

    const list = map.get(entry);
    if (list) list.push(mesh);
    else map.set(entry, [mesh]);
  });

  return map;
}
