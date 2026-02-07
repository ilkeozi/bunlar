import { Button } from '@/components/ui/button';
import { useAssemblyExplorerStore } from '../state/useAssemblyExplorerStore';
import { isLeafPartNode } from '../utils/nodeMapIndex';

export function AssemblyExplorerToolbar() {
  const nodeMap = useAssemblyExplorerStore((state) => state.nodeMap);
  const selectedNodeId = useAssemblyExplorerStore(
    (state) => state.selectedNodeId
  );
  const explicitHiddenNodeIds = useAssemblyExplorerStore(
    (state) => state.explicitHiddenNodeIds
  );
  const isolateActive = useAssemblyExplorerStore(
    (state) => state.isolateActive
  );
  const hideSelected = useAssemblyExplorerStore((state) => state.hideSelected);
  const showSelected = useAssemblyExplorerStore((state) => state.showSelected);
  const toggleIsolate = useAssemblyExplorerStore(
    (state) => state.toggleIsolate
  );
  const showAll = useAssemblyExplorerStore((state) => state.showAll);
  const requestFit = useAssemblyExplorerStore((state) => state.requestFit);

  const selectedNode =
    nodeMap && selectedNodeId ? nodeMap.nodes[selectedNodeId] : null;
  const canActOnSelection = Boolean(nodeMap && selectedNodeId);
  const canIsolate = Boolean(
    nodeMap && selectedNode && isLeafPartNode(selectedNode)
  );
  const canShowAll = Boolean(
    nodeMap && (explicitHiddenNodeIds.size > 0 || isolateActive)
  );
  const canFit = Boolean(nodeMap);

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        type="button"
        size="sm"
        variant="outline"
        disabled={!canActOnSelection}
        onClick={hideSelected}
      >
        Hide
      </Button>
      <Button
        type="button"
        size="sm"
        variant="outline"
        disabled={!canActOnSelection}
        onClick={showSelected}
      >
        Show
      </Button>
      <Button
        type="button"
        size="sm"
        variant={isolateActive ? 'default' : 'outline'}
        disabled={!canIsolate}
        onClick={toggleIsolate}
      >
        Isolate
      </Button>
      <Button
        type="button"
        size="sm"
        variant="outline"
        disabled={!canShowAll}
        onClick={showAll}
      >
        Show all
      </Button>
      <Button
        type="button"
        size="sm"
        variant="outline"
        disabled={!canFit}
        onClick={() => requestFit(selectedNodeId ? 'selection' : 'visible')}
      >
        Fit
      </Button>
    </div>
  );
}
