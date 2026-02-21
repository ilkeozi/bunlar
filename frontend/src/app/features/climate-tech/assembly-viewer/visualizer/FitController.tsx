import { useEffect, useRef } from 'react';
import { useThree } from '@react-three/fiber';
import type { RefObject } from 'react';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import * as THREE from 'three';
import { useAssemblyExplorerStore } from '../state/useAssemblyExplorerStore';
import { computeFitPosition } from '../utils/fitCamera';

function computeBoundsForMeshes(meshes: THREE.Mesh[]): THREE.Box3 | null {
  const bounds = new THREE.Box3();
  for (const mesh of meshes) bounds.expandByObject(mesh);
  return bounds.isEmpty() ? null : bounds;
}

function computeVisibleBounds(meshesByOcafEntry: Map<string, THREE.Mesh[]>) {
  const bounds = new THREE.Box3();
  let count = 0;
  for (const meshes of meshesByOcafEntry.values()) {
    for (const mesh of meshes) {
      if (!mesh.visible) continue;
      bounds.expandByObject(mesh);
      count += 1;
    }
  }
  return count === 0 || bounds.isEmpty() ? null : bounds;
}

function easeInOutQuad(t: number) {
  if (t < 0.5) return 2 * t * t;
  return 1 - Math.pow(-2 * t + 2, 2) / 2;
}

export function FitController({
  controlsRef,
}: {
  controlsRef: RefObject<OrbitControlsImpl | null>;
}) {
  const camera = useThree((state) => state.camera);
  const fitRequestId = useAssemblyExplorerStore((s) => s.fitRequestId);

  const animationRef = useRef<{ token: number; rafId: number | null }>({
    token: 0,
    rafId: null,
  });

  useEffect(() => {
    if (fitRequestId === 0) return;
    if (!(camera instanceof THREE.PerspectiveCamera)) return;
    if (!controlsRef.current) return;

    const { fitRequestMode, selectedOcafEntry, meshesByOcafEntry } =
      useAssemblyExplorerStore.getState();
    if (!fitRequestMode) return;
    if (!meshesByOcafEntry) return;

    const bounds =
      fitRequestMode === 'selection'
        ? (() => {
            if (!selectedOcafEntry) return null;
            const meshes = meshesByOcafEntry.get(selectedOcafEntry) ?? [];
            return meshes.length ? computeBoundsForMeshes(meshes) : null;
          })()
        : computeVisibleBounds(meshesByOcafEntry);
    if (!bounds) return;

    const target = controlsRef.current.target.clone();
    const nextPosition = computeFitPosition({
      camera,
      target,
      bounds,
      margin: 1.15,
    });
    if (!nextPosition) return;

    animationRef.current.token += 1;
    const token = animationRef.current.token;

    if (animationRef.current.rafId !== null) {
      cancelAnimationFrame(animationRef.current.rafId);
      animationRef.current.rafId = null;
    }

    const from = camera.position.clone();
    const to = nextPosition.clone();
    const start = performance.now();
    const durationMs = 300;

    const tick = (now: number) => {
      if (animationRef.current.token !== token) return;
      const t = Math.min(1, (now - start) / durationMs);
      const eased = easeInOutQuad(t);
      camera.position.lerpVectors(from, to, eased);
      camera.updateMatrixWorld();
      controlsRef.current?.update();

      if (t < 1) {
        animationRef.current.rafId = requestAnimationFrame(tick);
      } else {
        animationRef.current.rafId = null;
      }
    };

    animationRef.current.rafId = requestAnimationFrame(tick);

    return () => {
      if (animationRef.current.rafId !== null) {
        cancelAnimationFrame(animationRef.current.rafId);
        animationRef.current.rafId = null;
      }
    };
  }, [camera, controlsRef, fitRequestId]);

  return null;
}
