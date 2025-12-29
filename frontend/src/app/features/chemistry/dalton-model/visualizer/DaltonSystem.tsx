import { useEffect, useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { Group } from 'three';
import type { ElementDetails } from '../../../../data/elements';
import { SoftLightRig } from './SoftLightRig';
import { useDaltonStore } from '../state/useDaltonStore';
import { useAtomColors } from './useAtomColors';

interface DaltonSystemProps {
  element: ElementDetails;
}

const MAX_ATOMIC_MASS = 250;
const MIN_RADIUS = 1.6;
const MAX_RADIUS = 3.2;

export function DaltonSystem({ element }: DaltonSystemProps) {
  const rotateAtom = useDaltonStore((state) => state.view.rotateAtom);
  const freezeMotion = useDaltonStore((state) => state.view.freezeMotion);
  const colors = useAtomColors();
  const groupRef = useRef<Group>(null);

  const geometry = useMemo(() => {
    return new THREE.SphereGeometry(getDaltonRadius(element.atomicMass), 64, 64);
  }, [element.atomicMass]);

  const material = useMemo(() => {
    return new THREE.MeshStandardMaterial({
      color: colors.neutron,
      emissive: colors.nucleusGlow,
      emissiveIntensity: 0.12,
      roughness: 0.35,
      metalness: 0.08,
    });
  }, [colors]);

  useEffect(() => {
    return () => {
      geometry.dispose();
      material.dispose();
    };
  }, [geometry, material]);

  useFrame((_, delta) => {
    if (!rotateAtom || freezeMotion || !groupRef.current) {
      return;
    }

    groupRef.current.rotation.y += delta * 0.2;
    groupRef.current.rotation.x += delta * 0.08;
  });

  return (
    <group ref={groupRef}>
      <SoftLightRig />
      <mesh geometry={geometry} material={material} />
    </group>
  );
}

function getDaltonRadius(atomicMass: number) {
  const clampedMass = Math.max(1, Math.min(atomicMass, MAX_ATOMIC_MASS));
  const normalized = Math.cbrt(clampedMass) / Math.cbrt(MAX_ATOMIC_MASS);
  return MIN_RADIUS + normalized * (MAX_RADIUS - MIN_RADIUS);
}
