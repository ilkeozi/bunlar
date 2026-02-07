import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AssemblyExplorerToolbar } from './AssemblyExplorerToolbar';
import { AssemblyExplorerTree } from './AssemblyExplorerTree';
import { useAssemblyExplorerStore } from '../state/useAssemblyExplorerStore';
import { useTranslation } from '../../../../i18n/useTranslation';

export function AssemblyExplorerPanel() {
  const { t } = useTranslation();
  const nodeMap = useAssemblyExplorerStore((state) => state.nodeMap);

  if (!nodeMap) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('assemblyViewer.explorer.title')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <AssemblyExplorerToolbar />
        <AssemblyExplorerTree />
      </CardContent>
    </Card>
  );
}
