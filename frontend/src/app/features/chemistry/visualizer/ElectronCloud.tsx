import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { Line } from '@react-three/drei';
import type { ElectronParticle } from '../../../utils/particle-distribution';
import type { ElectronShell } from '../../../data/elements';
import { useFrame } from '@react-three/fiber';
import { useAtomColors } from './useAtomColors';
import { createGlowSpriteMaterial } from './glowTextures';

interface ElectronCloudProps {
  shells: ElectronShell[];
  electrons: ElectronParticle[];
  showTrails: boolean;
}

interface ElectronRuntimeConfig {
  radius: number;
  speed: number;
  verticalAmplitude: number;
  phase: number;
  quaternion: THREE.Quaternion;
  shellIndex: number;
}

const ORBIT_SEGMENTS = 72;

export function ElectronCloud({ shells, electrons, showTrails }: ElectronCloudProps) {
  const colors = useAtomColors();
  const orbitColor = colors.electronOrbit;
  const electronRefs = useRef<THREE.Group[]>([]);

  const shellOrientations = useMemo(() => {
    return shells.map((shell) => {
      const baseTilt = 0.18 + shell.index * 0.07;
      const tiltX = (shell.index % 2 === 0 ? 1 : -1) * baseTilt;
      const tiltY = shell.index * 0.28;
      const quaternion = new THREE.Quaternion().setFromEuler(new THREE.Euler(tiltX, tiltY, 0));
      return { tiltX, tiltY, quaternion };
    });
  }, [shells]);

  const runtimeConfig = useMemo<ElectronRuntimeConfig[]>(() => {
    const configs: ElectronRuntimeConfig[] = [];

    shells.forEach((shell) => {
      const orientation = shellOrientations[shell.index];
      const baseSpeed = 0.55 + shell.index * 0.22;
      const verticalAmplitude = shell.radius * 0.075;

      electrons
        .filter((electron) => electron.shellIndex === shell.index)
        .forEach((electron) => {
          configs.push({
            radius: shell.radius,
            speed: baseSpeed,
            verticalAmplitude,
            phase: electron.phase,
            quaternion: orientation.quaternion,
            shellIndex: shell.index,
          });
        });
    });

    return configs;
  }, [shells, electrons, shellOrientations]);

  const orbitPoints = useMemo(() => {
    const byIndex: Record<number, THREE.Vector3[]> = {};
    shells.forEach((shell) => {
      byIndex[shell.index] = buildCirclePoints(shell.radius, ORBIT_SEGMENTS);
    });
    return byIndex;
  }, [shells]);

  const tempPosition = useMemo(() => new THREE.Vector3(), []);
  const electronGeometry = useMemo(() => new THREE.SphereGeometry(0.2, 12, 12), []);
  const electronMaterial = useMemo(
    () => new THREE.MeshBasicMaterial({ color: colors.electron }),
    [colors.electron]
  );
  const electronGlowMaterial = useMemo(
    () => createGlowSpriteMaterial(colors.electron, 0.8, 0),
    [colors.electron]
  );

  useEffect(() => {
    return () => {
      electronGeometry.dispose();
      electronMaterial.dispose();
      electronGlowMaterial.dispose();
    };
  }, [electronGeometry, electronMaterial, electronGlowMaterial]);

  useEffect(() => {
    electronRefs.current.length = runtimeConfig.length;
  }, [runtimeConfig.length]);

  useFrame((state, delta) => {
    const time = state.clock.elapsedTime + delta;

    runtimeConfig.forEach((config, index) => {
      const holder = electronRefs.current[index];
      if (!holder) {
        return;
      }

      const angle = time * config.speed + config.phase;

      tempPosition.set(
        Math.cos(angle) * config.radius,
        Math.sin(angle * 0.65 + config.phase * 0.45) * config.verticalAmplitude,
        Math.sin(angle) * config.radius
      );

      tempPosition.applyQuaternion(config.quaternion);

      holder.position.copy(tempPosition);
    });
  });

  return (
    <group name="electron-cloud">
      {shells.map((shell) => {
        const orientation = shellOrientations[shell.index];
        const points = orbitPoints[shell.index];
        return (
          <group key={shell.index} rotation={[orientation.tiltX, orientation.tiltY, 0]}>
            {showTrails && shell.electrons > 0 && points && (
              <Line
                points={points}
                color={orbitColor}
                lineWidth={0.95}
                transparent
                opacity={0.22 + shell.occupancyRatio * 0.35}
              />
            )}
          </group>
        );
      })}

      <group>
        {runtimeConfig.map((config, index) => (
          <group
            key={`electron-${config.shellIndex}-${index}`}
            ref={(group) => {
              if (group) {
                electronRefs.current[index] = group;
              } else {
                delete electronRefs.current[index];
              }
            }}
          >
            <mesh geometry={electronGeometry} material={electronMaterial} />
            <sprite material={electronGlowMaterial} scale={[0.6, 0.6, 0.6]} />
          </group>
        ))}
      </group>
    </group>
  );
}

function buildCirclePoints(radius: number, segments = ORBIT_SEGMENTS) {
  const points: THREE.Vector3[] = [];
  for (let i = 0; i <= segments; i += 1) {
    const theta = (i / segments) * Math.PI * 2;
    points.push(new THREE.Vector3(Math.cos(theta) * radius, 0, Math.sin(theta) * radius));
  }
  return points;
}
