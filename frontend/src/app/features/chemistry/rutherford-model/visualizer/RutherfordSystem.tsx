import { useEffect, useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import type { Group } from 'three';
import type { ElementDetails } from '../../../../data/elements';
import { SoftLightRig } from './SoftLightRig';
import { useRutherfordStore } from '../state/useRutherfordStore';
import { useAtomColors } from './useAtomColors';

interface RutherfordSystemProps {
  element: ElementDetails;
}

const MAX_ATOMIC_MASS = 250;
const MIN_ORBIT_RADIUS = 4;
const MAX_ORBIT_RADIUS = 9;

export function RutherfordSystem({ element }: RutherfordSystemProps) {
  const rotateAtom = useRutherfordStore((state) => state.view.rotateAtom);
  const freezeMotion = useRutherfordStore((state) => state.view.freezeMotion);
  const showTrails = useRutherfordStore((state) => state.view.showElectronTrails);
  const colors = useAtomColors();
  const groupRef = useRef<Group>(null);
  const electronsRef = useRef<THREE.InstancedMesh>(null);
  const motionTime = useRef(0);
  const orbitColor = colors.electronOrbit;

  const nucleusRadius = useMemo(() => {
    const clampedMass = Math.max(1, Math.min(element.atomicMass, MAX_ATOMIC_MASS));
    return Math.max(0.55, Math.cbrt(clampedMass) * 0.18);
  }, [element.atomicMass]);

  const nucleusGeometry = useMemo(() => new THREE.SphereGeometry(nucleusRadius, 24, 24), [nucleusRadius]);
  const nucleusMaterial = useMemo(() => {
    return new THREE.MeshStandardMaterial({
      color: colors.proton,
      emissive: colors.nucleusGlow,
      emissiveIntensity: 0.18,
      roughness: 0.3,
      metalness: 0.1,
    });
  }, [colors]);

  const orbitConfigs = useMemo(() => {
    const count = Math.max(element.electrons, 1);
    const random = mulberry32(element.atomicNumber || 1);
    const configs: Array<{
      radius: number;
      speed: number;
      phase: number;
      quaternion: THREE.Quaternion;
    }> = [];

    for (let i = 0; i < count; i += 1) {
      const t = count === 1 ? 0 : i / (count - 1);
      const radius = MIN_ORBIT_RADIUS + Math.pow(t, 0.75) * (MAX_ORBIT_RADIUS - MIN_ORBIT_RADIUS);
      const speed = 0.7 / (1 + t * 1.6);
      const phase = random() * Math.PI * 2;
      const normal = randomUnitVector(random);
      const quaternion = new THREE.Quaternion().setFromUnitVectors(
        new THREE.Vector3(0, 1, 0),
        normal
      );

      configs.push({ radius, speed, phase, quaternion });
    }

    return configs;
  }, [element.atomicNumber, element.electrons]);

  const orbitPaths = useMemo(() => {
    return orbitConfigs.map((config) => buildOrbitPoints(config.radius, config.quaternion));
  }, [orbitConfigs]);

  const electronRadius = useMemo(() => 0.18, []);
  const electronGeometry = useMemo(() => new THREE.SphereGeometry(electronRadius, 12, 12), [electronRadius]);
  const electronMaterial = useMemo(() => {
    return new THREE.MeshStandardMaterial({
      color: colors.electron,
      emissive: colors.electron,
      emissiveIntensity: 0.6,
      roughness: 0.2,
      metalness: 0.05,
    });
  }, [colors]);

  useEffect(() => {
    return () => {
      nucleusGeometry.dispose();
      nucleusMaterial.dispose();
      electronGeometry.dispose();
      electronMaterial.dispose();
    };
  }, [nucleusGeometry, nucleusMaterial, electronGeometry, electronMaterial]);

  useFrame((_, delta) => {
    if (!freezeMotion) {
      motionTime.current += delta;
    }

    const time = motionTime.current;
    const electronsMesh = electronsRef.current;
    if (!electronsMesh) {
      return;
    }

    const tempObject = new THREE.Object3D();
    orbitConfigs.forEach((config, index) => {
      const angle = time * config.speed + config.phase;
      const position = new THREE.Vector3(
        Math.cos(angle) * config.radius,
        0,
        Math.sin(angle) * config.radius
      );
      position.applyQuaternion(config.quaternion);
      tempObject.position.copy(position);
      tempObject.updateMatrix();
      electronsMesh.setMatrixAt(index, tempObject.matrix);
    });
    electronsMesh.instanceMatrix.needsUpdate = true;

    if (rotateAtom && !freezeMotion && groupRef.current) {
      groupRef.current.rotation.y += delta * 0.15;
    }
  });

  return (
    <group ref={groupRef}>
      <SoftLightRig />
      <mesh geometry={nucleusGeometry} material={nucleusMaterial} />
      {showTrails &&
        orbitPaths.map((points, index) => (
          <Line
            key={`orbit-${index}`}
            points={points}
            color={orbitColor}
            lineWidth={0.9}
            transparent
            opacity={0.2}
          />
        ))}
      <instancedMesh
        ref={electronsRef}
        args={[electronGeometry, electronMaterial, orbitConfigs.length]}
      />
    </group>
  );
}

function randomUnitVector(random: () => number) {
  const u = random();
  const v = random();
  const theta = u * Math.PI * 2;
  const phi = Math.acos(2 * v - 1);
  const sinPhi = Math.sin(phi);
  return new THREE.Vector3(
    sinPhi * Math.cos(theta),
    Math.cos(phi),
    sinPhi * Math.sin(theta)
  );
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

function buildOrbitPoints(radius: number, quaternion: THREE.Quaternion, segments = 96) {
  const points: THREE.Vector3[] = [];
  for (let i = 0; i <= segments; i += 1) {
    const theta = (i / segments) * Math.PI * 2;
    const point = new THREE.Vector3(Math.cos(theta) * radius, 0, Math.sin(theta) * radius);
    point.applyQuaternion(quaternion);
    points.push(point);
  }
  return points;
}
