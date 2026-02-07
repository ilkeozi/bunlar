import { create } from 'zustand';
import type * as THREE from 'three';
import type { AssemblyNodeMap } from '../types';

export type AssemblyExplorerSelectionSource = 'tree' | '3d' | 'program';
export type AssemblyExplorerFitRequestMode = 'selection' | 'visible';

type MeshIndex = Map<string, THREE.Mesh[]>;

type AssemblyExplorerState = {
  nodeMap: AssemblyNodeMap | null;
  selectedNodeId: string | null;
  selectedOcafEntry: string | null;
  selectionSource: AssemblyExplorerSelectionSource;
  expandedNodeIds: Set<string>;
  explicitHiddenNodeIds: Set<string>;
  isolateActive: boolean;
  isolateSnapshot: Set<string> | null;
  fitRequestId: number;
  fitRequestMode: AssemblyExplorerFitRequestMode | null;
  meshesByOcafEntry: MeshIndex | null;

  setNodeMap: (nodeMap: AssemblyNodeMap | null) => void;
  selectNodeId: (
    nodeId: string | null,
    source: AssemblyExplorerSelectionSource
  ) => void;
  selectOcafEntry: (
    ocafEntry: string | null,
    source: AssemblyExplorerSelectionSource
  ) => void;
  toggleExpanded: (nodeId: string) => void;
  toggleHidden: (nodeId: string) => void;
  hideSelected: () => void;
  showSelected: () => void;
  toggleIsolate: () => void;
  showAll: () => void;
  requestFit: (mode: AssemblyExplorerFitRequestMode) => void;
  setMeshesByOcafEntry: (meshesByOcafEntry: MeshIndex | null) => void;
};

function isLeafPartNode(
  node: { kind: string; children: string[] } | null | undefined
): boolean {
  return node?.kind === 'part' && (node.children?.length ?? 0) === 0;
}

function getAncestorNodeIdsRootFirst(
  nodeMap: AssemblyNodeMap,
  nodeId: string
): string[] {
  const ancestors: string[] = [];
  let cursor = nodeMap.nodes[nodeId];
  while (cursor?.parentId) {
    ancestors.push(cursor.parentId);
    cursor = nodeMap.nodes[cursor.parentId];
  }
  ancestors.reverse();
  return ancestors;
}

export const useAssemblyExplorerStore = create<AssemblyExplorerState>(
  (set, get) => {
    let nodeIdByOcafEntry = new Map<string, string>();

    return {
      nodeMap: null,
      selectedNodeId: null,
      selectedOcafEntry: null,
      selectionSource: 'program',
      expandedNodeIds: new Set(),
      explicitHiddenNodeIds: new Set(),
      isolateActive: false,
      isolateSnapshot: null,
      fitRequestId: 0,
      fitRequestMode: null,
      meshesByOcafEntry: null,

      setNodeMap: (nodeMap) => {
        nodeIdByOcafEntry = new Map();

        if (!nodeMap) {
          set(() => ({
            nodeMap: null,
            selectedNodeId: null,
            selectedOcafEntry: null,
            selectionSource: 'program',
            expandedNodeIds: new Set(),
            explicitHiddenNodeIds: new Set(),
            isolateActive: false,
            isolateSnapshot: null,
          }));
          return;
        }

        for (const [nodeId, node] of Object.entries(nodeMap.nodes)) {
          if (!isLeafPartNode(node)) continue;
          if (!node.labelEntry) continue;
          if (!nodeIdByOcafEntry.has(node.labelEntry))
            nodeIdByOcafEntry.set(node.labelEntry, nodeId);
        }

        set((state) => {
          const next: Partial<AssemblyExplorerState> = { nodeMap };

          const selectionOcafEntry = state.selectedOcafEntry;
          if (selectionOcafEntry && !state.selectedNodeId) {
            const resolved = nodeIdByOcafEntry.get(selectionOcafEntry) ?? null;
            if (resolved) next.selectedNodeId = resolved;
          }

          if (
            state.selectedNodeId &&
            !(state.selectedNodeId in nodeMap.nodes)
          ) {
            const resolved = selectionOcafEntry
              ? nodeIdByOcafEntry.get(selectionOcafEntry) ?? null
              : null;
            next.selectedNodeId = resolved;
            if (!resolved) next.selectedOcafEntry = null;
          }

          return { ...state, ...next };
        });
      },

      selectNodeId: (nodeId, source) => {
        const nodeMap = get().nodeMap;
        if (!nodeMap) {
          set((state) =>
            state.selectedNodeId === null &&
            state.selectedOcafEntry === null &&
            state.selectionSource === source
              ? state
              : {
                  ...state,
                  selectedNodeId: null,
                  selectedOcafEntry: null,
                  selectionSource: source,
                }
          );
          return;
        }

        if (!nodeId) {
          set((state) =>
            state.selectedNodeId === null &&
            state.selectedOcafEntry === null &&
            state.selectionSource === source
              ? state
              : {
                  ...state,
                  selectedNodeId: null,
                  selectedOcafEntry: null,
                  selectionSource: source,
                }
          );
          return;
        }

        const node = nodeMap.nodes[nodeId];
        if (source === 'tree' && !isLeafPartNode(node)) return;

        const ocafEntry = node?.labelEntry ?? null;
        set((state) =>
          state.selectedNodeId === nodeId &&
          state.selectedOcafEntry === ocafEntry &&
          state.selectionSource === source
            ? state
            : {
                ...state,
                selectedNodeId: nodeId,
                selectedOcafEntry: ocafEntry,
                selectionSource: source,
              }
        );
      },

      selectOcafEntry: (ocafEntry, source) => {
        if (!ocafEntry) {
          set((state) =>
            state.selectedNodeId === null &&
            state.selectedOcafEntry === null &&
            state.selectionSource === source
              ? state
              : {
                  ...state,
                  selectedNodeId: null,
                  selectedOcafEntry: null,
                  selectionSource: source,
                }
          );
          return;
        }

        const nodeMap = get().nodeMap;
        const resolvedNodeId = nodeIdByOcafEntry.get(ocafEntry) ?? null;

        set((state) => {
          const nextExpanded =
            source === '3d' && nodeMap && resolvedNodeId
              ? (() => {
                  const ancestors = getAncestorNodeIdsRootFirst(
                    nodeMap,
                    resolvedNodeId
                  );
                  if (ancestors.length === 0) return state.expandedNodeIds;
                  const merged = new Set(state.expandedNodeIds);
                  for (const id of ancestors) merged.add(id);
                  return merged;
                })()
              : state.expandedNodeIds;

          const didChangeExpansion = nextExpanded !== state.expandedNodeIds;
          const didChangeSelection =
            state.selectedOcafEntry !== ocafEntry ||
            state.selectedNodeId !== resolvedNodeId;
          const didChangeSource = state.selectionSource !== source;

          if (!didChangeExpansion && !didChangeSelection && !didChangeSource)
            return state;

          return {
            ...state,
            selectedOcafEntry: ocafEntry,
            selectedNodeId: resolvedNodeId,
            selectionSource: source,
            expandedNodeIds: nextExpanded,
          };
        });
      },

      toggleExpanded: (nodeId) => {
        set((state) => {
          const next = new Set(state.expandedNodeIds);
          if (next.has(nodeId)) next.delete(nodeId);
          else next.add(nodeId);
          return next.size === state.expandedNodeIds.size
            ? state
            : { ...state, expandedNodeIds: next };
        });
      },

      toggleHidden: (nodeId) => {
        set((state) => {
          const next = new Set(state.explicitHiddenNodeIds);
          if (next.has(nodeId)) next.delete(nodeId);
          else next.add(nodeId);
          return next.size === state.explicitHiddenNodeIds.size
            ? state
            : { ...state, explicitHiddenNodeIds: next };
        });
      },

      hideSelected: () => {
        const selectedNodeId = get().selectedNodeId;
        if (!selectedNodeId) return;
        set((state) => {
          if (state.explicitHiddenNodeIds.has(selectedNodeId)) return state;
          const next = new Set(state.explicitHiddenNodeIds);
          next.add(selectedNodeId);
          return { ...state, explicitHiddenNodeIds: next };
        });
      },

      showSelected: () => {
        const selectedNodeId = get().selectedNodeId;
        if (!selectedNodeId) return;
        set((state) => {
          if (!state.explicitHiddenNodeIds.has(selectedNodeId)) return state;
          const next = new Set(state.explicitHiddenNodeIds);
          next.delete(selectedNodeId);
          return { ...state, explicitHiddenNodeIds: next };
        });
      },

      toggleIsolate: () => {
        const nodeMap = get().nodeMap;
        const selectedNodeId = get().selectedNodeId;
        if (!nodeMap || !selectedNodeId) return;
        const selectedNode = nodeMap.nodes[selectedNodeId];
        if (!isLeafPartNode(selectedNode)) return;

        set((state) => {
          if (state.isolateActive) {
            return {
              ...state,
              isolateActive: false,
              explicitHiddenNodeIds: state.isolateSnapshot
                ? new Set(state.isolateSnapshot)
                : state.explicitHiddenNodeIds,
              isolateSnapshot: null,
            };
          }

          const snapshot = new Set(state.explicitHiddenNodeIds);
          const hidden = new Set<string>();
          for (const [nodeId, node] of Object.entries(nodeMap.nodes)) {
            if (!isLeafPartNode(node)) continue;
            if (nodeId !== selectedNodeId) hidden.add(nodeId);
          }

          return {
            ...state,
            isolateActive: true,
            isolateSnapshot: snapshot,
            explicitHiddenNodeIds: hidden,
          };
        });
      },

      showAll: () => {
        set((state) =>
          state.explicitHiddenNodeIds.size === 0 &&
          !state.isolateActive &&
          state.isolateSnapshot === null
            ? state
            : {
                ...state,
                explicitHiddenNodeIds: new Set(),
                isolateActive: false,
                isolateSnapshot: null,
              }
        );
      },

      requestFit: (mode) => {
        set((state) => ({
          ...state,
          fitRequestId: state.fitRequestId + 1,
          fitRequestMode: mode,
        }));
      },

      setMeshesByOcafEntry: (meshesByOcafEntry) => {
        set((state) =>
          state.meshesByOcafEntry === meshesByOcafEntry
            ? state
            : { ...state, meshesByOcafEntry }
        );
      },
    };
  }
);
