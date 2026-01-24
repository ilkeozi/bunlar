import * as THREE from 'three';

export function centerModel(model: THREE.Object3D) {
  const bounds = new THREE.Box3().setFromObject(model);
  const center = bounds.getCenter(new THREE.Vector3());
  model.position.sub(center);
  model.updateMatrixWorld(true);
  return model;
}
