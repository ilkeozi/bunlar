import { memo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { ElementDetails, ElectronShell } from '../../../data/elements';
import { useTranslation } from '../../../i18n/useTranslation';

interface ElementStatsProps {
  element: ElementDetails;
  shells: ElectronShell[];
}

export const ElementStats = memo(function ElementStats({ element, shells }: ElementStatsProps) {
  const { t, translateCategory } = useTranslation();

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle>{element.name}</CardTitle>
        <CardDescription>{translateCategory(element.category)}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {t('stats.atomicNumber')}
            </dt>
            <dd className="mt-1 text-base font-semibold text-foreground">{element.atomicNumber}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {t('stats.atomicMass')}
            </dt>
            <dd className="mt-1 text-base font-semibold text-foreground">
              {element.atomicMass.toFixed(3)}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {t('stats.protons')}
            </dt>
            <dd className="mt-1 text-base font-semibold text-foreground">{element.protons}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {t('stats.neutrons')}
            </dt>
            <dd className="mt-1 text-base font-semibold text-foreground">{element.neutrons}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {t('stats.electrons')}
            </dt>
            <dd className="mt-1 text-base font-semibold text-foreground">{element.electrons}</dd>
          </div>
        </dl>

        <div className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t('stats.shells')}
          </h3>
          <ul className="space-y-3">
            {shells.map((shell) => (
              <li key={shell.index} className="space-y-2">
                <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                  <span>n = {shell.index + 1}</span>
                  <span className="text-sm font-semibold text-foreground">
                    {shell.electrons}
                    <span className="ml-1 text-xs text-muted-foreground">/{shell.capacity}</span>
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted/40">
                  <span
                    className="block h-full rounded-full bg-primary"
                    style={{ width: `${shell.occupancyRatio * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
});
