import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { useAssemblyExplorerStore } from '../state/useAssemblyExplorerStore';

const OUTLINE_NAME = 'selected-part-outline';

type OutlineAttachment = {
  outline: THREE.LineSegments;
  edges: THREE.EdgesGeometry;
  material: THREE.LineBasicMaterial;
};

export function SelectionOutline() {
  const selectedOcafEntry = useAssemblyExplorerStore(
    (state) => state.selectedOcafEntry
  );
  const meshesByOcafEntry = useAssemblyExplorerStore(
    (state) => state.meshesByOcafEntry
  );

  const attachmentsRef = useRef<OutlineAttachment[]>([]);

  useEffect(() => {
    const attachments = attachmentsRef.current;
    attachmentsRef.current = [];

    for (const { outline, edges, material } of attachments) {
      if (outline.parent) outline.parent.remove(outline);
      edges.dispose();
      material.dispose();
    }

    if (!selectedOcafEntry || !meshesByOcafEntry) return;
    const meshes = meshesByOcafEntry.get(selectedOcafEntry);
    if (!meshes || meshes.length === 0) return;

    const next: OutlineAttachment[] = [];
    for (const mesh of meshes) {
      const edges = new THREE.EdgesGeometry(mesh.geometry, 35);
      const material = new THREE.LineBasicMaterial({
        color: '#7dd3fc',
        transparent: true,
        opacity: 1,
      });
      material.depthTest = false;
      material.depthWrite = false;

      const outline = new THREE.LineSegments(edges, material);
      outline.name = OUTLINE_NAME;
      outline.raycast = () => {};
      outline.scale.setScalar(1.03);
      mesh.add(outline);

      next.push({ outline, edges, material });
    }

    attachmentsRef.current = next;

    return () => {
      const current = attachmentsRef.current;
      attachmentsRef.current = [];

      for (const { outline, edges, material } of current) {
        if (outline.parent) outline.parent.remove(outline);
        edges.dispose();
        material.dispose();
      }
    };
  }, [meshesByOcafEntry, selectedOcafEntry]);

  return null;
}
