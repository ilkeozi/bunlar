import { useMemo, useRef } from 'react';
import type { Group } from 'three';
import { useFrame } from '@react-three/fiber';
import type { ElementDetails, ElectronShell } from '../../../data/elements';
import { Nucleus } from './Nucleus';
import { ElectronCloud } from './ElectronCloud';
import { SoftLightRig } from './SoftLightRig';
import { useAtomStore } from '../state/useAtomStore';
import { createElectronPhases, generateNucleusLayout } from './utils/particle-distribution';

interface AtomSystemProps {
  element: ElementDetails;
  shells: ElectronShell[];
}

export function AtomSystem({ element, shells }: AtomSystemProps) {
  const showTrails = useAtomStore((state) => state.view.showElectronTrails);

  const nucleusParticles = useMemo(() => {
    return generateNucleusLayout(element.protons, element.neutrons);
  }, [element.protons, element.neutrons]);

  const electronPhases = useMemo(() => {
    const distribution = shells.map((shell) => shell.electrons);
    return createElectronPhases(distribution);
  }, [shells]);

  const groupRef = useRef<Group>(null);

  useFrame((_state, delta) => {
    const group = groupRef.current;
    if (!group) {
      return;
    }
    group.rotation.y += delta * 0.05;
  });

  return (
    <group ref={groupRef}>
      <SoftLightRig />
      <Nucleus particles={nucleusParticles} />
      <ElectronCloud shells={shells} electrons={electronPhases} showTrails={showTrails} />
    </group>
  );
}
