import { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import type { NucleusParticle } from './utils/particle-distribution';
import { useAtomColors } from './useAtomColors';
import { createGlowSpriteMaterial } from './glowTextures';

interface NucleusProps {
  particles: NucleusParticle[];
}

export function Nucleus({ particles }: NucleusProps) {
  const colors = useAtomColors();
  const coreRadius = useMemo(() => {
    return Math.max(0.7, Math.cbrt(Math.max(particles.length, 1)) * 0.34);
  }, [particles.length]);

  const sphereGeometry = useMemo(() => new THREE.SphereGeometry(0.26, 12, 12), []);
  const protonMaterial = useMemo(() => new THREE.MeshBasicMaterial({ color: colors.proton }), [colors.proton]);
  const neutronMaterial = useMemo(() => new THREE.MeshBasicMaterial({ color: colors.neutron }), [colors.neutron]);
  const protonGlowMaterial = useMemo(() => createGlowSpriteMaterial(colors.proton, 1.1, 0), [colors.proton]);
  const neutronGlowMaterial = useMemo(() => createGlowSpriteMaterial(colors.neutron, 0.95, 0), [colors.neutron]);

  useEffect(() => {
    return () => {
      sphereGeometry.dispose();
      protonMaterial.dispose();
      neutronMaterial.dispose();
      protonGlowMaterial.dispose();
      neutronGlowMaterial.dispose();
    };
  }, [sphereGeometry, protonMaterial, neutronMaterial, protonGlowMaterial, neutronGlowMaterial]);

  return (
    <group name="nucleus">
      {particles.map((particle) => (
        <group
          key={particle.index}
          position={[particle.position.x, particle.position.y, particle.position.z]}
          scale={[particle.scale, particle.scale, particle.scale]}
        >
          <mesh
            geometry={sphereGeometry}
            material={particle.type === 'proton' ? protonMaterial : neutronMaterial}
          />
          <sprite
            material={particle.type === 'proton' ? protonGlowMaterial : neutronGlowMaterial}
            scale={[0.7, 0.7, 0.7]}
          />
        </group>
      ))}

      <mesh scale={coreRadius * 1.3}>
        <sphereGeometry args={[1, 16, 16]} />
        <meshBasicMaterial color={colors.nucleusGlow} transparent opacity={0.12} />
      </mesh>
    </group>
  );
}
