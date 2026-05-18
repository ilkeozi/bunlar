import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import type { Group } from 'three';
import type { ElementDetails, ElectronShell } from '../../../../data/elements';
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
  const rotateAtom = useAtomStore((state) => state.view.rotateAtom);
  const tiltedOrbits = useAtomStore((state) => state.view.tiltedOrbits);
  const freezeMotion = useAtomStore((state) => state.view.freezeMotion);
  const groupRef = useRef<Group>(null);

  const nucleusParticles = useMemo(() => {
    return generateNucleusLayout(element.protons, element.neutrons);
  }, [element.protons, element.neutrons]);

  const electronPhases = useMemo(() => {
    const distribution = shells.map((shell) => shell.electrons);
    return createElectronPhases(distribution);
  }, [shells]);

  useFrame((_, delta) => {
    if (!rotateAtom || freezeMotion || !groupRef.current) {
      return;
    }

    groupRef.current.rotation.y += delta * 0.25;
  });

  return (
    <group ref={groupRef}>
      <SoftLightRig />
      <Nucleus particles={nucleusParticles} />
      <ElectronCloud
        shells={shells}
        electrons={electronPhases}
        showTrails={showTrails}
        tiltedOrbits={tiltedOrbits}
        freezeMotion={freezeMotion}
      />
    </group>
  );
}
