import type { AssemblyNodeMap } from '../types';

type NodeId = string;
type AssemblyNode = AssemblyNodeMap['nodes'][NodeId];

export function isLeafPartNode(node: AssemblyNode | null | undefined): boolean {
  return node?.kind === 'part' && (node.children?.length ?? 0) === 0;
}

/**
 * Returns all ancestor node ids for `nodeId`, ordered root-first.
 * The returned list excludes `nodeId` itself.
 */
export function getAncestorNodeIds(
  nodeMap: AssemblyNodeMap,
  nodeId: NodeId
): NodeId[] {
  const ancestors: NodeId[] = [];
  let cursor = nodeMap.nodes[nodeId];

  while (cursor?.parentId) {
    ancestors.push(cursor.parentId);
    cursor = nodeMap.nodes[cursor.parentId];
  }

  ancestors.reverse();
  return ancestors;
}

/**
 * Returns all descendant node ids in the subtree of `nodeId`.
 * The returned list excludes `nodeId` itself.
 */
export function getDescendantNodeIds(
  nodeMap: AssemblyNodeMap,
  nodeId: NodeId
): NodeId[] {
  const start = nodeMap.nodes[nodeId];
  if (!start) return [];

  const out: NodeId[] = [];
  const queue: NodeId[] = [...(start.children ?? [])];

  while (queue.length) {
    const id = queue.shift() as NodeId;
    out.push(id);
    const node = nodeMap.nodes[id];
    if (node?.children?.length) queue.push(...node.children);
  }

  return out;
}

/**
 * Returns leaf-part node ids in the subtree rooted at `nodeId`.
 * Includes `nodeId` itself if it is a leaf part.
 */
export function getLeafPartNodeIdsInSubtree(
  nodeMap: AssemblyNodeMap,
  nodeId: NodeId
): NodeId[] {
  const start = nodeMap.nodes[nodeId];
  if (!start) return [];

  const out: NodeId[] = [];
  const stack: NodeId[] = [nodeId];

  while (stack.length) {
    const id = stack.pop() as NodeId;
    const node = nodeMap.nodes[id];
    if (!node) continue;
    if (isLeafPartNode(node)) out.push(id);
    if (node.children?.length) {
      for (let i = node.children.length - 1; i >= 0; i -= 1)
        stack.push(node.children[i]);
    }
  }

  return out;
}

export function buildNodeIdByOcafEntry(
  nodeMap: AssemblyNodeMap
): Map<string, NodeId> {
  const map = new Map<string, NodeId>();

  const queue: NodeId[] = [...(nodeMap.roots ?? [])];
  while (queue.length) {
    const id = queue.shift() as NodeId;
    const node = nodeMap.nodes[id];
    if (!node) continue;

    if (isLeafPartNode(node)) {
      const entry = node.labelEntry;
      if (typeof entry === 'string' && entry.length > 0 && !map.has(entry))
        map.set(entry, id);
    }

    if (node.children?.length) queue.push(...node.children);
  }

  return map;
}

export function getEffectiveHiddenLeafPartNodeIds(
  nodeMap: AssemblyNodeMap,
  explicitHiddenNodeIds: Set<NodeId>
): Set<NodeId> {
  const out = new Set<NodeId>();

  for (const hiddenId of explicitHiddenNodeIds) {
    const leafIds = getLeafPartNodeIdsInSubtree(nodeMap, hiddenId);
    for (const leafId of leafIds) out.add(leafId);
  }

  return out;
}

export function getEffectiveHiddenLeafPartOcafEntries(
  nodeMap: AssemblyNodeMap,
  explicitHiddenNodeIds: Set<NodeId>
): Set<string> {
  const leafIds = getEffectiveHiddenLeafPartNodeIds(
    nodeMap,
    explicitHiddenNodeIds
  );
  const out = new Set<string>();

  for (const leafId of leafIds) {
    const node = nodeMap.nodes[leafId];
    const entry = node?.labelEntry;
    if (typeof entry === 'string' && entry.length > 0) out.add(entry);
  }

  return out;
}

// Alias used by some consumers (generic name).
export const getEffectiveHidden = getEffectiveHiddenLeafPartNodeIds;
