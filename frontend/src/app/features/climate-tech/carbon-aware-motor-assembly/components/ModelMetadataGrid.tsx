import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useTranslation } from '../../../../i18n/useTranslation';
import type { AssemblyGroup, HierarchyItem, PartGroup } from '../types';

interface ModelMetadataGridProps {
  hierarchy: HierarchyItem[];
  partGroups: PartGroup[];
  assemblyGroups: AssemblyGroup[];
}

export function ModelMetadataGrid({
  hierarchy,
  partGroups,
  assemblyGroups,
}: ModelMetadataGridProps) {
  const { t } = useTranslation();

  return (
    <section className="grid gap-6 xl:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle>{t('controls.modelHierarchyTitle')}</CardTitle>
          <CardDescription>
            {t('controls.modelHierarchyDescription')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {hierarchy.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              {t('controls.modelHierarchyEmpty')}
            </p>
          ) : (
            <div className="max-h-72 overflow-auto rounded-lg border border-border/60 bg-background/40 p-3 text-xs text-muted-foreground">
              {hierarchy.map((item, index) => (
                <div
                  key={`${item.name}-${index}`}
                  className="flex items-center gap-2 py-1"
                  style={{ paddingLeft: `${item.depth * 12}px` }}
                >
                  <span className="text-foreground/80">{item.name}</span>
                  <span className="text-muted-foreground/70">({item.type})</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{t('controls.partGroupsTitle')}</CardTitle>
          <CardDescription>{t('controls.partGroupsDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          {partGroups.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              {t('controls.partGroupsEmpty')}
            </p>
          ) : (
            <div className="max-h-72 overflow-auto rounded-lg border border-border/60 bg-background/40 p-3 text-xs text-muted-foreground">
              {partGroups.map((group) => {
                const topAssembly = group.assemblies[0];
                return (
                  <div key={group.key} className="space-y-1 py-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-foreground/80">{group.name}</span>
                      <span className="text-muted-foreground/70">
                        ×{group.count}
                      </span>
                    </div>
                    {topAssembly && (
                      <div className="text-[11px] text-muted-foreground/70">
                        {t('controls.partGroupsTopAssembly')}{' '}
                        {topAssembly.name} ({topAssembly.count})
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{t('controls.assemblyGroupsTitle')}</CardTitle>
          <CardDescription>
            {t('controls.assemblyGroupsDescription')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {assemblyGroups.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              {t('controls.assemblyGroupsEmpty')}
            </p>
          ) : (
            <div className="max-h-64 overflow-auto rounded-lg border border-border/60 bg-background/40 p-3 text-xs text-muted-foreground">
              {assemblyGroups.map((group) => (
                <div key={`${group.path}/${group.name}`} className="py-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-foreground/80">{group.name}</span>
                    <span className="text-muted-foreground/70">
                      {group.meshCount}
                    </span>
                  </div>
                  <div className="text-[11px] text-muted-foreground/70">
                    {group.path}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
