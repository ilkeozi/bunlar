import { describe, expect, it } from 'vitest';
import * as THREE from 'three';

import { indexMeshesByOcafEntry } from './sceneIndex';

describe('indexMeshesByOcafEntry', () => {
  it('indexes meshes by OCAF entry found on an ancestor node name', () => {
    const root = new THREE.Group();
    root.name = 'Root [0:1:1:1]';

    const mesh = new THREE.Mesh(
      new THREE.BoxGeometry(1, 1, 1),
      new THREE.MeshBasicMaterial()
    );
    mesh.name = '';
    root.add(mesh);

    const map = indexMeshesByOcafEntry(root);
    expect(map.get('0:1:1:1')?.length).toBe(1);
  });
});
