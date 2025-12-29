import { memo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { ElementDetails } from '../../../../data/elements';
import { useTranslation } from '../../../../i18n/useTranslation';

interface ElementStatsProps {
  element: ElementDetails;
}

export const ElementStats = memo(function ElementStats({ element }: ElementStatsProps) {
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
      </CardContent>
    </Card>
  );
});
