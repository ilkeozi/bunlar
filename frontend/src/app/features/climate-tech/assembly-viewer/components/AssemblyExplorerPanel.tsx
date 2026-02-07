import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AssemblyExplorerToolbar } from './AssemblyExplorerToolbar';
import { AssemblyExplorerTree } from './AssemblyExplorerTree';
import { useAssemblyExplorerStore } from '../state/useAssemblyExplorerStore';

export function AssemblyExplorerPanel() {
  const nodeMap = useAssemblyExplorerStore((state) => state.nodeMap);

  if (!nodeMap) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Explorer</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <AssemblyExplorerToolbar />
        <AssemblyExplorerTree />
      </CardContent>
    </Card>
  );
}
