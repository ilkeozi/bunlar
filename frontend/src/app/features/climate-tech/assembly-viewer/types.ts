import type { BomExport, BomItem, BomOccurrence, NodeMap } from 'opencascade-convert/browser';

export type AssemblyNodeMap = NodeMap;
export type AssemblyBom = BomExport;
export type AssemblyMetadata<N extends NodeMap = NodeMap> = {
  bom: BomExportWithNodeMap<N>;
  nodeMap: N;
};

type NodeId<N extends NodeMap> = keyof N['nodes'] & string;

export type BomOccurrenceWithNodeMap<N extends NodeMap> = Omit<BomOccurrence, 'nodeId'> & {
  nodeId: NodeId<N>;
};

export type BomItemWithNodeMap<N extends NodeMap> = Omit<BomItem, 'instances'> & {
  instances: BomOccurrenceWithNodeMap<N>[];
};

export type BomExportWithNodeMap<N extends NodeMap> = Omit<BomExport, 'items'> & {
  items: BomItemWithNodeMap<N>[];
};

export function isBomLinkedToNodeMap<N extends NodeMap>(
  nodeMap: N,
  bom: BomExport
): bom is BomExportWithNodeMap<N> {
  return bom.items.every((item) =>
    item.instances.every((instance) => instance.nodeId in nodeMap.nodes)
  );
}

export type TranslateFn = (key: import('../../../i18n/translations').TranslationKey) => string;
