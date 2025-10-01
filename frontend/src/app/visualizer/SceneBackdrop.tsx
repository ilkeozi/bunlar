import { Grid, Stars } from '@react-three/drei';

export function SceneBackdrop() {
  return (
    <group>
      <Stars
        radius={120}
        depth={60}
        count={2500}
        factor={4}
        saturation={0.7}
        fade
      />
      <Grid
        position={[0, -8, 0]}
        args={[60, 60]}
        fadeStrength={1.5}
        cellColor="#22324f"
        cellThickness={0.5}
        sectionColor="#1f3352"
        infiniteGrid
      />
    </group>
  );
}
