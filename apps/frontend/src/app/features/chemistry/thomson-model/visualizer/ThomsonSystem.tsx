import { useEffect, useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { Group } from 'three';
import type { ElementDetails } from '../../../../data/elements';
import { SoftLightRig } from './SoftLightRig';
import { useThomsonStore } from '../state/useThomsonStore';
import { useAtomColors } from './useAtomColors';

interface ThomsonSystemProps {
  element: ElementDetails;
}

const MAX_ATOMIC_MASS = 250;
const MIN_RADIUS = 1.6;
const MAX_RADIUS = 3.2;

export function ThomsonSystem({ element }: ThomsonSystemProps) {
  const rotateAtom = useThomsonStore((state) => state.view.rotateAtom);
  const freezeMotion = useThomsonStore((state) => state.view.freezeMotion);
  const showPositiveSphere = useThomsonStore((state) => state.view.showPositiveSphere);
  const cutawaySphere = useThomsonStore((state) => state.view.cutawaySphere);
  const colors = useAtomColors();
  const groupRef = useRef<Group>(null);
  const electronsRef = useRef<THREE.InstancedMesh>(null);

  const radius = useMemo(() => {
    return getThomsonRadius(element.atomicMass);
  }, [element.atomicMass]);

  const electronPositions = useMemo(() => {
    return createElectronPositions(element.electrons, radius * 0.78, element.atomicNumber);
  }, [element.atomicNumber, element.electrons, radius]);

  const sphereGeometry = useMemo(() => new THREE.SphereGeometry(radius, 64, 64), [radius]);
  const sphereMaterial = useMemo(() => {
    return new THREE.MeshStandardMaterial({
      color: colors.proton,
      emissive: colors.nucleusGlow,
      emissiveIntensity: 0.12,
      roughness: 0.25,
      metalness: 0.04,
      transparent: true,
      opacity: 0.45,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
  }, [colors]);
  const sphereWireMaterial = useMemo(() => {
    return new THREE.MeshBasicMaterial({
      color: colors.proton,
      transparent: true,
      opacity: 0.25,
      wireframe: true,
    });
  }, [colors.proton]);
  const clipPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(1, 0, 0), 0), []);

  const electronRadius = useMemo(() => Math.max(0.16, radius * 0.08), [radius]);
  const electronGeometry = useMemo(
    () => new THREE.SphereGeometry(electronRadius, 12, 12),
    [electronRadius]
  );
  const electronMaterial = useMemo(() => {
    return new THREE.MeshStandardMaterial({
      color: colors.electron,
      emissive: colors.electron,
      emissiveIntensity: 0.7,
      roughness: 0.2,
      metalness: 0.05,
    });
  }, [colors]);

  useEffect(() => {
    const electronsMesh = electronsRef.current;
    if (!electronsMesh) {
      return;
    }

    const tempObject = new THREE.Object3D();
    electronPositions.forEach((position, index) => {
      tempObject.position.copy(position);
      tempObject.updateMatrix();
      electronsMesh.setMatrixAt(index, tempObject.matrix);
    });
    electronsMesh.instanceMatrix.needsUpdate = true;
  }, [electronPositions]);

  useEffect(() => {
    if (cutawaySphere) {
      sphereMaterial.clippingPlanes = [clipPlane];
      sphereWireMaterial.clippingPlanes = [clipPlane];
    } else {
      sphereMaterial.clippingPlanes = null;
      sphereWireMaterial.clippingPlanes = null;
    }
    sphereMaterial.needsUpdate = true;
    sphereWireMaterial.needsUpdate = true;
  }, [cutawaySphere, clipPlane, sphereMaterial, sphereWireMaterial]);

  useEffect(() => {
    return () => {
      sphereGeometry.dispose();
      sphereMaterial.dispose();
      sphereWireMaterial.dispose();
      electronGeometry.dispose();
      electronMaterial.dispose();
    };
  }, [sphereGeometry, sphereMaterial, sphereWireMaterial, electronGeometry, electronMaterial]);

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
      {showPositiveSphere && (
        <>
          <mesh geometry={sphereGeometry} material={sphereMaterial} renderOrder={2} />
          <mesh geometry={sphereGeometry} material={sphereWireMaterial} scale={1.01} renderOrder={3} />
        </>
      )}
      <instancedMesh
        ref={electronsRef}
        args={[electronGeometry, electronMaterial, electronPositions.length]}
        renderOrder={1}
      />
    </group>
  );
}

function getThomsonRadius(atomicMass: number) {
  const clampedMass = Math.max(1, Math.min(atomicMass, MAX_ATOMIC_MASS));
  const normalized = Math.cbrt(clampedMass) / Math.cbrt(MAX_ATOMIC_MASS);
  return MIN_RADIUS + normalized * (MAX_RADIUS - MIN_RADIUS);
}

function createElectronPositions(count: number, radius: number, seed: number) {
  const positions: THREE.Vector3[] = [];
  const random = mulberry32(seed || 1);

  for (let i = 0; i < count; i += 1) {
    const u = random();
    const v = random();
    const theta = u * Math.PI * 2;
    const phi = Math.acos(2 * v - 1);
    const r = Math.cbrt(random()) * radius;
    const sinPhi = Math.sin(phi);

    positions.push(
      new THREE.Vector3(
        r * sinPhi * Math.cos(theta),
        r * Math.cos(phi),
        r * sinPhi * Math.sin(theta)
      )
    );
  }

  return positions;
}

function mulberry32(seed: number) {
  let t = seed;
  return () => {
    t += 0x6d2b79f5;
    let value = Math.imul(t ^ (t >>> 15), 1 | t);
    value ^= value + Math.imul(value ^ (value >>> 7), 61 | value);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}
