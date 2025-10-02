import { useMemo, useCallback, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text, useCursor } from '@react-three/drei';
import type { ElementDetails } from '../data/elements';
import { ELEMENTS } from '../data/elements';
import { useAtomStore } from '../state/useAtomStore';
import { PERIODIC_POSITIONS, type ElementGridPosition } from './periodicLayout';

interface PositionedElement {
  element: ElementDetails;
  grid: ElementGridPosition;
  position: [number, number, number];
}

const CATEGORY_COLORS: Record<string, string> = {
  'Alkali metal': '#f4a6a3',
  'Alkaline earth metal': '#f7d488',
  Lanthanide: '#f4b77d',
  Actinide: '#f09f9c',
  'Transition metal': '#c8c58c',
  'Post-transition metal': '#a8c9e2',
  Metalloid: '#d6d3c4',
  Nonmetal: '#9ed7a7',
  'Noble gas': '#b6a0c7',
  Halogen: '#f6b1c3',
};

const CUBE_SIZE = 1.2;
const HALF_CUBE = CUBE_SIZE / 2;
const FACE_OFFSET = HALF_CUBE + 0.06;
const STICKER_SIZE = CUBE_SIZE * 0.86;
const STICKER_Z_OFFSET = 0.002;

interface FaceStickerProps {
  element: ElementDetails;
  scale: number;
  position: [number, number, number];
  rotation: [number, number, number];
}

function FaceSticker({ element, scale, position, rotation }: FaceStickerProps) {
  const scaledPosition: [number, number, number] = [position[0] * scale, position[1] * scale, position[2] * scale];
  return (
    <group position={scaledPosition} rotation={rotation}>
      <mesh>
        <planeGeometry args={[STICKER_SIZE, STICKER_SIZE]} />
        <meshBasicMaterial color="#f8f9ff" toneMapped={false} />
      </mesh>

      <Text
        position={[0, STICKER_SIZE * 0.28, STICKER_Z_OFFSET]}
        fontSize={0.16}
        color="#202431"
        anchorX="center"
        anchorY="middle"
      >
        Z {element.atomicNumber}
      </Text>

      <Text
        position={[0, STICKER_SIZE * 0.08, STICKER_Z_OFFSET]}
        fontSize={0.34}
        color="#0b0d12"
        anchorX="center"
        anchorY="middle"
      >
        {element.symbol}
      </Text>

      <Text
        position={[0, -STICKER_SIZE * 0.16, STICKER_Z_OFFSET]}
        fontSize={0.18}
        color="#202431"
        anchorX="center"
        anchorY="middle"
        maxWidth={0.92}
      >
        {element.name}
      </Text>
    </group>
  );
}

interface ElementMarkerProps {
  item: PositionedElement;
  isSelected: boolean;
  onSelect: (symbol: string) => void;
}

function ElementMarker({ item, isSelected, onSelect }: ElementMarkerProps) {
  const [hovered, setHovered] = useState(false);
  useCursor(hovered, 'pointer');

  const handleSelect = useCallback(() => onSelect(item.element.symbol), [item.element.symbol, onSelect]);

  const color = CATEGORY_COLORS[item.element.category] ?? '#9fb4ff';
  const scale = isSelected ? 1.08 : hovered ? 1.02 : 1;
  const cubeScale: [number, number, number] = [scale, scale, scale];

  return (
    <group position={item.position}>
      <mesh
        scale={cubeScale}
        onClick={(event) => {
          event.stopPropagation();
          handleSelect();
        }}
        onPointerOver={(event) => {
          event.stopPropagation();
          setHovered(true);
        }}
        onPointerOut={() => setHovered(false)}
        castShadow={false}
        receiveShadow={false}
      >
        <boxGeometry args={[CUBE_SIZE, CUBE_SIZE, CUBE_SIZE]} />
        <meshStandardMaterial color={color} metalness={0.15} roughness={0.6} />
      </mesh>

      <FaceSticker
        element={item.element}
        scale={scale}
        position={[0, FACE_OFFSET, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
      />
    </group>
  );
}

export function PeriodicCanvas() {
  const selectedSymbol = useAtomStore((state) => state.selectedSymbol);
  const selectElement = useAtomStore((state) => state.selectElement);

  const positionedElements = useMemo<PositionedElement[]>(() => {
    const spacing = 1.85;
    const elementsWithPositions = ELEMENTS.map((element) => {
      const grid = PERIODIC_POSITIONS[element.symbol];
      if (!grid) {
        return undefined;
      }

      const x = (grid.column - 9.5) * spacing;
      const z = (grid.row - 4) * spacing;
      const y = 0;

      return {
        element,
        grid,
        position: [x, y, z] as [number, number, number],
      } satisfies PositionedElement;
    });

    return elementsWithPositions.filter((item): item is PositionedElement => Boolean(item));
  }, []);

  return (
    <div className="h-full w-full">
      <Canvas
        shadows={false}
        dpr={[1, 1.5]}
        camera={{ position: [0, 26, 42], fov: 45 }}
      >
        <color attach="background" args={[0x05070d]} />
        <hemisphereLight args={[0xffffff, 0x222533, 0.55]} />
        <directionalLight position={[30, 50, 20]} intensity={0.6} />
        <directionalLight position={[-25, 35, -25]} intensity={0.35} />

        {positionedElements.map((item) => (
          <ElementMarker
            key={item.element.symbol}
            item={item}
            isSelected={item.element.symbol === selectedSymbol}
            onSelect={selectElement}
          />
        ))}

        <OrbitControls
          enableDamping
          dampingFactor={0.06}
          enablePan
          panSpeed={0.8}
          minDistance={18}
          maxDistance={60}
          maxPolarAngle={Math.PI / 2.1}
        />
      </Canvas>
    </div>
  );
}
