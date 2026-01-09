import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useFrame, type ThreeEvent } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import partsCatalog from '../../../../data/climate-tech/partsCatalog.json';
import type {
  AssemblyGroup,
  HierarchyItem,
  PartMaterialMeta,
  PartGroup,
  PcfOverlayMode,
  SelectedPart,
} from '../types';
import {
  applyMaterial,
  createDebugMaterial,
  createMaterialIndex,
  createMaterialLibrary,
  resolveMaterial,
} from './materials';
import {
  buildExplodeParts,
  collectAssemblyGroups,
  collectHierarchy,
  collectPartGroups,
  normalizeMatchKey,
  normalizeMatchKeyLoose,
  normalizePartName,
  type ExplodePart,
} from './modeling';

const GEARBOX_MODEL_URL = '/models/blender.glb';
const DEBUG_MATERIAL_GUESS = 'steel_fastener_12_9';

export function GearboxModel({
  explode,
  debugMaterials,
  pcfOverlayMode,
  pcfMaxByMode,
  selectedMesh,
  onPartSelect,
  onPartsCount,
  onHierarchy,
  onPartGroups,
  onAssemblyGroups,
}: {
  explode: number;
  debugMaterials: boolean;
  pcfOverlayMode: PcfOverlayMode;
  pcfMaxByMode: Record<PcfOverlayMode, number>;
  selectedMesh?: THREE.Mesh | null;
  onPartSelect?: (selection: SelectedPart | null) => void;
  onPartsCount?: (count: number) => void;
  onHierarchy?: (items: HierarchyItem[]) => void;
  onPartGroups?: (groups: PartGroup[]) => void;
  onAssemblyGroups?: (groups: AssemblyGroup[]) => void;
}) {
  const { scene } = useGLTF(GEARBOX_MODEL_URL);
  const overlayEnabled = pcfOverlayMode !== 'none';
  const currentMaxPcf = pcfMaxByMode[pcfOverlayMode] ?? 0;
  const outlineRef = useRef<THREE.LineSegments | null>(null);
  const isMesh = useCallback(
    (object: THREE.Object3D): object is THREE.Mesh =>
      (object as THREE.Mesh).isMesh === true,
    []
  );
  const isLight = useCallback(
    (object: THREE.Object3D): object is THREE.Light =>
      (object as THREE.Light).isLight === true,
    []
  );
  const materialLibrary = useMemo(
    () =>
      createMaterialLibrary(
        (partsCatalog.materials as Record<
          string,
          {
            color: string;
            metalness: number;
            roughness: number;
            envMapIntensity?: number;
          }
        >) ?? {}
      ),
    []
  );
  const materialIndex = useMemo(
    () => createMaterialIndex(partsCatalog.parts ?? []),
    []
  );
  const debugMaterial = useMemo(() => createDebugMaterial(), []);
  const overlayCache = useRef(new Map<string, THREE.MeshStandardMaterial>());
  const hasLoggedUnmatched = useRef(false);
  const currentExplode = useRef(explode);
  const targetExplode = useRef(explode);
  const findMetaForMesh = useCallback(
    (rawName: string): PartMaterialMeta | undefined => {
      if (!rawName) {
        return undefined;
      }
      const trimmed = rawName.trim();
      const normalized = normalizePartName(trimmed);
      const matchKey = normalizeMatchKey(trimmed);
      const looseKey = normalizeMatchKeyLoose(trimmed);
      return (
        materialIndex.get(normalized.toLowerCase()) ??
        materialIndex.get(trimmed.toLowerCase()) ??
        materialIndex.get(matchKey) ??
        materialIndex.get(looseKey)
      );
    },
    [materialIndex]
  );
  const model = useMemo(() => {
    const cloned = scene.clone(true);
    const lights: THREE.Light[] = [];
    cloned.traverse((child) => {
      if (isLight(child)) {
        lights.push(child);
      }
    });
    lights.forEach((light) => light.parent?.remove(light));

    const box = new THREE.Box3().setFromObject(cloned);
    const center = box.getCenter(new THREE.Vector3());
    cloned.position.sub(center);
    cloned.rotation.z = Math.PI / 2;
    cloned.updateMatrixWorld(true);

    return cloned;
  }, [isLight, scene]);

  useEffect(() => {
    overlayCache.current.clear();
  }, [pcfOverlayMode, currentMaxPcf]);

  useEffect(() => {
    targetExplode.current = explode;
  }, [explode]);

  useEffect(() => {
    const unmatched = new Set<string>();
    model.traverse((child) => {
      if (!isMesh(child)) {
        return;
      }
      const rawName = child.name?.trim() ?? '';
      const normalized = normalizePartName(rawName);
      const matchKey = normalizeMatchKey(rawName);
      const looseKey = normalizeMatchKeyLoose(rawName);
      const meta =
        materialIndex.get(normalized.toLowerCase()) ??
        materialIndex.get(rawName.toLowerCase()) ??
        materialIndex.get(matchKey) ??
        materialIndex.get(looseKey);
      if (!meta && rawName) {
        unmatched.add(rawName);
      }
      applyMaterial(
        child,
        resolveMaterial(materialLibrary, meta, {
          enabled: debugMaterials,
          material: debugMaterial,
          targetMaterialGuess: DEBUG_MATERIAL_GUESS,
        }, {
          enabled: overlayEnabled,
          mode: pcfOverlayMode,
          maxPcf: currentMaxPcf,
          cache: overlayCache.current,
        })
      );
    });
    if (
      !hasLoggedUnmatched.current &&
      unmatched.size > 0 &&
      import.meta.env.DEV
    ) {
      hasLoggedUnmatched.current = true;
      console.warn(
        `[GearboxModel] Unmatched mesh names (${unmatched.size}):`,
        Array.from(unmatched).sort()
      );
    }
  }, [
    applyMaterial,
    debugMaterial,
    debugMaterials,
    hasLoggedUnmatched,
    isMesh,
    materialIndex,
    materialLibrary,
    model,
    normalizePartName,
    currentMaxPcf,
    overlayEnabled,
    pcfOverlayMode,
    resolveMaterial,
  ]);

  const parts: ExplodePart[] = useMemo(
    () => buildExplodeParts(model, isMesh),
    [isMesh, model]
  );
  const hierarchy = useMemo(() => collectHierarchy(model), [model]);
  const partGroups = useMemo(
    () => collectPartGroups(model, isMesh),
    [isMesh, model]
  );
  const assemblyGroups = useMemo(
    () => collectAssemblyGroups(model, isMesh),
    [isMesh, model]
  );

  useEffect(() => {
    onPartsCount?.(parts.length);
    onHierarchy?.(hierarchy);
    onPartGroups?.(partGroups);
    onAssemblyGroups?.(assemblyGroups);
  }, [
    onAssemblyGroups,
    onHierarchy,
    onPartGroups,
    onPartsCount,
    assemblyGroups,
    hierarchy,
    partGroups,
    parts.length,
  ]);

  useFrame((_, delta) => {
    const nextExplode = THREE.MathUtils.damp(
      currentExplode.current,
      targetExplode.current,
      10,
      delta
    );
    currentExplode.current = nextExplode;
    const distance = nextExplode * 2;
    parts.forEach(({ object, base, dir, magnitude }) => {
      object.position.copy(base).addScaledVector(dir, distance * magnitude);
    });
  });

  const handlePointerDown = useCallback(
    (event: ThreeEvent<PointerEvent>) => {
      event.stopPropagation();
      if (!isMesh(event.object)) {
        return;
      }
      const meta = findMetaForMesh(event.object.name ?? '');
      onPartSelect?.({
        mesh: event.object,
        meta,
      });
    },
    [findMetaForMesh, isMesh, onPartSelect]
  );

  useEffect(() => {
    if (outlineRef.current?.parent) {
      outlineRef.current.parent.remove(outlineRef.current);
      outlineRef.current.geometry.dispose();
      const previousMaterial = outlineRef.current.material;
      if (Array.isArray(previousMaterial)) {
        previousMaterial.forEach((mat) => mat.dispose());
      } else {
        previousMaterial.dispose();
      }
      outlineRef.current = null;
    }

    if (!selectedMesh) {
      return;
    }

    const edges = new THREE.EdgesGeometry(selectedMesh.geometry, 35);
    const material = new THREE.LineBasicMaterial({
      color: '#7dd3fc',
      transparent: true,
      opacity: 1,
    });
    material.depthTest = false;
    material.depthWrite = false;
    const outline = new THREE.LineSegments(edges, material);
    outline.name = 'selected-part-outline';
    outline.raycast = () => {};
    outline.scale.setScalar(1.03);
    selectedMesh.add(outline);
    outlineRef.current = outline;

    return () => {
      if (outline.parent) {
        outline.parent.remove(outline);
      }
      outline.geometry.dispose();
      material.dispose();
    };
  }, [selectedMesh]);

  return <primitive object={model} onPointerDown={handlePointerDown} />;
}

useGLTF.preload(GEARBOX_MODEL_URL);
