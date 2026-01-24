import { Badge } from '@/components/ui/badge';
import type { TranslateFn } from '../types';

type StepConverterHeaderProps = {
  t: TranslateFn;
  badgeKey?: Parameters<TranslateFn>[0];
  titleKey?: Parameters<TranslateFn>[0];
  subtitleKey?: Parameters<TranslateFn>[0];
};

export function StepConverterHeader({
  t,
  badgeKey = 'tools.stepConverter.badge',
  titleKey = 'tools.stepConverter.title',
  subtitleKey = 'tools.stepConverter.subtitle',
}: StepConverterHeaderProps) {
  return (
    <header className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="border-border/60 text-[11px] uppercase tracking-wide">
          {t('subjects.tools.title')}
        </Badge>
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {t(badgeKey)}
        </span>
      </div>
      <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">{t(titleKey)}</h2>
      <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
        {t(subtitleKey)}
      </p>
    </header>
  );
}
