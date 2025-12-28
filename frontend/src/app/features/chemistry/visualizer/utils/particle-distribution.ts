import * as THREE from 'three';

export interface NucleusParticle {
  index: number;
  type: 'proton' | 'neutron';
  position: THREE.Vector3;
  scale: number;
}

export interface ElectronParticle {
  shellIndex: number;
  electronIndex: number;
  phase: number;
}

export function generateNucleusLayout(protons: number, neutrons: number): NucleusParticle[] {
  const total = Math.max(1, protons + neutrons);
  const radius = Math.max(0.6, Math.cbrt(total) * 0.33);
  const vectors = fibonacciSphere(total, radius * 0.75);
  const particles: NucleusParticle[] = [];

  for (let i = 0; i < protons; i += 1) {
    particles.push({
      index: i,
      type: 'proton',
      position: vectors[i]?.clone() ?? new THREE.Vector3(),
      scale: 1,
    });
  }

  for (let j = 0; j < neutrons; j += 1) {
    const index = protons + j;
    particles.push({
      index,
      type: 'neutron',
      position: vectors[index]?.clone() ?? new THREE.Vector3(),
      scale: 1,
    });
  }

  return particles;
}

export function createElectronPhases(shellSizes: number[]): ElectronParticle[] {
  const particles: ElectronParticle[] = [];

  shellSizes.forEach((count, shellIndex) => {
    for (let electronIndex = 0; electronIndex < count; electronIndex += 1) {
      particles.push({
        shellIndex,
        electronIndex,
        phase: (electronIndex / Math.max(1, count)) * Math.PI * 2,
      });
    }
  });

  return particles;
}

function fibonacciSphere(count: number, radius: number): THREE.Vector3[] {
  if (count <= 1) {
    return [new THREE.Vector3(0, 0, 0)];
  }

  const result: THREE.Vector3[] = [];
  const offset = 2 / count;
  const increment = Math.PI * (3 - Math.sqrt(5));

  for (let i = 0; i < count; i += 1) {
    const y = (i * offset - 1) + offset / 2;
    const r = Math.sqrt(Math.max(0, 1 - y * y));
    const phi = i * increment;
    const x = Math.cos(phi) * r;
    const z = Math.sin(phi) * r;
    result.push(new THREE.Vector3(x * radius, y * radius, z * radius));
  }

  return result;
}
