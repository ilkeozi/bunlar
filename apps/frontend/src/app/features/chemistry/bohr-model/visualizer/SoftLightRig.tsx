import { useEffect } from 'react';
import { Color, HemisphereLight } from 'three';
import { useThree } from '@react-three/fiber';
import { useAtomColors } from './useAtomColors';

export function SoftLightRig() {
  const { scene } = useThree();
  const colors = useAtomColors();

  useEffect(() => {
    scene.background = new Color(colors.background);
    const hemi = new HemisphereLight('#6fb9ff', '#031025', 0.35);
    scene.add(hemi);
    return () => {
      scene.remove(hemi);
    };
  }, [scene]);

  return (
    <group>
      <directionalLight
        position={[6, 10, 8]}
        intensity={2.2}
      />
      <directionalLight position={[-9, -5, -6]} intensity={1.4} color={0x90aaff} />
      <pointLight position={[0, 5, -10]} intensity={0.7} color={0xff7744} decay={1.5} distance={70} />
    </group>
  );
}
