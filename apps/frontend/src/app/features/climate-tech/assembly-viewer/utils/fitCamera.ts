import * as THREE from 'three';

export function computeFitPosition(params: {
  camera: THREE.PerspectiveCamera;
  target: THREE.Vector3;
  bounds: THREE.Box3;
  margin?: number;
}): THREE.Vector3 | null {
  const { camera, target, bounds, margin = 1.15 } = params;
  const sphere = bounds.getBoundingSphere(new THREE.Sphere());
  const radius = sphere.radius * margin;
  if (!Number.isFinite(radius) || radius <= 0) return null;

  const vFov = THREE.MathUtils.degToRad(camera.fov);
  const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
  const fov = Math.min(vFov, hFov);
  const distance = radius / Math.sin(fov / 2);

  const dir = camera.position.clone().sub(target).normalize();
  if (!Number.isFinite(dir.lengthSq()) || dir.lengthSq() <= 0) return null;

  return target.clone().addScaledVector(dir, distance);
}
