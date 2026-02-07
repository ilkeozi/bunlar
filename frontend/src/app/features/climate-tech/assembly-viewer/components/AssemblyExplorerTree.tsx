import { useEffect, useRef } from 'react';
import type { AssemblyNodeMap } from '../types';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronRight, Eye, EyeOff } from 'lucide-react';
import { useAssemblyExplorerStore } from '../state/useAssemblyExplorerStore';
import { cn } from '@/lib/utils';
import { isLeafPartNode } from '../utils/nodeMapIndex';

type NodeId = string;

function isNodeEffectivelyHidden(
  nodeMap: AssemblyNodeMap,
  nodeId: NodeId,
  explicitHiddenNodeIds: Set<NodeId>
) {
  let cursor: NodeId | null = nodeId;
  while (cursor) {
    if (explicitHiddenNodeIds.has(cursor)) return true;
    cursor = nodeMap.nodes[cursor]?.parentId ?? null;
  }
  return false;
}

export function AssemblyExplorerTree() {
  const nodeMap = useAssemblyExplorerStore((state) => state.nodeMap);
  const selectedNodeId = useAssemblyExplorerStore(
    (state) => state.selectedNodeId
  );
  const selectionSource = useAssemblyExplorerStore(
    (state) => state.selectionSource
  );
  const expandedNodeIds = useAssemblyExplorerStore(
    (state) => state.expandedNodeIds
  );
  const explicitHiddenNodeIds = useAssemblyExplorerStore(
    (state) => state.explicitHiddenNodeIds
  );
  const toggleExpanded = useAssemblyExplorerStore(
    (state) => state.toggleExpanded
  );
  const toggleHidden = useAssemblyExplorerStore((state) => state.toggleHidden);
  const selectNodeId = useAssemblyExplorerStore((state) => state.selectNodeId);

  const rowRefs = useRef<Map<NodeId, HTMLDivElement>>(new Map());

  useEffect(() => {
    if (!nodeMap) return;
    if (!selectedNodeId) return;
    if (selectionSource !== '3d') return;

    const nodeEl = rowRefs.current.get(selectedNodeId);
    if (!nodeEl) return;

    const raf = requestAnimationFrame(() => {
      nodeEl.scrollIntoView({ block: 'nearest' });
    });
    return () => cancelAnimationFrame(raf);
  }, [nodeMap, selectedNodeId, selectionSource]);

  if (!nodeMap) return null;

  const renderNode = (nodeId: NodeId, depth: number) => {
    const node = nodeMap.nodes[nodeId];
    if (!node) return <></>;

    const hasChildren = (node.children?.length ?? 0) > 0;
    const isExpanded = expandedNodeIds.has(nodeId);
    const selectable = isLeafPartNode(node);
    const isSelected = selectedNodeId === nodeId;
    const isExplicitHidden = explicitHiddenNodeIds.has(nodeId);
    const isHiddenEffective = isNodeEffectivelyHidden(
      nodeMap,
      nodeId,
      explicitHiddenNodeIds
    );

    return (
      <div key={nodeId}>
        <div
          ref={(el) => {
            if (el) rowRefs.current.set(nodeId, el);
            else rowRefs.current.delete(nodeId);
          }}
          className={cn(
            'group flex w-full items-center gap-1.5 rounded-md px-1.5 py-1 text-left text-xs transition-colors',
            selectable
              ? 'cursor-pointer hover:bg-muted/60'
              : 'cursor-pointer hover:bg-muted/40',
            isSelected ? 'bg-muted' : null
          )}
          style={{ paddingLeft: depth * 12 }}
          role="button"
          tabIndex={0}
          onClick={() => {
            if (selectable) {
              selectNodeId(nodeId, 'tree');
            } else if (hasChildren) {
              toggleExpanded(nodeId);
            }
          }}
          onKeyDown={(event) => {
            if (event.key !== 'Enter' && event.key !== ' ') return;
            event.preventDefault();
            if (selectable) {
              selectNodeId(nodeId, 'tree');
            } else if (hasChildren) {
              toggleExpanded(nodeId);
            }
          }}
        >
          <span className="flex h-5 w-5 items-center justify-center">
            {hasChildren ? (
              isExpanded ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )
            ) : null}
          </span>

          <span
            className={cn(
              'min-w-0 flex-1 truncate',
              isHiddenEffective ? 'text-muted-foreground' : null
            )}
            title={node.name}
          >
            {node.name}
          </span>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={cn(
              'h-7 w-7 text-muted-foreground hover:text-foreground',
              isHiddenEffective ? 'opacity-80' : 'opacity-60',
              isExplicitHidden ? 'opacity-100' : null
            )}
            onClick={(event) => {
              event.stopPropagation();
              toggleHidden(nodeId);
            }}
            aria-label={isExplicitHidden ? 'Show node' : 'Hide node'}
          >
            {isExplicitHidden ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </Button>
        </div>
        {hasChildren && isExpanded
          ? node.children.map((childId) => renderNode(childId, depth + 1))
          : null}
      </div>
    );
  };

  return (
    <div className="max-h-[520px] overflow-auto rounded-lg border border-border/60 bg-background/50 p-2">
      {nodeMap.roots.map((rootId) => renderNode(rootId, 0))}
    </div>
  );
}
