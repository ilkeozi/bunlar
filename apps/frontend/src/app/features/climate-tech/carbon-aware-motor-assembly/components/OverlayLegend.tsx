import { useTranslation } from '../../../../i18n/useTranslation';
import { cn } from '@/lib/utils';
import type { PcfOverlayMode } from '../types';

interface OverlayLegendProps {
  enabled: boolean;
  overlayModeLabel: string;
  maxValue: number;
  className?: string;
  mode: PcfOverlayMode;
}

export function OverlayLegend({
  enabled,
  overlayModeLabel,
  maxValue,
  className,
  mode,
}: OverlayLegendProps) {
  const { t } = useTranslation();

  if (!enabled || mode === 'none') {
    return null;
  }

  return (
    <div
      className={cn(
        'pointer-events-none rounded-xl border border-border/50 bg-slate-950/60 p-3 text-xs text-muted-foreground shadow-lg backdrop-blur',
        className
      )}
    >
      <div>
        {t('controls.pcfOverlayMode')}: {overlayModeLabel} (
        {t('controls.pcfLegendUnit')})
      </div>
      <div className="mt-2 flex items-center justify-between text-[11px]">
        <span>{t('controls.pcfLegendLow')}</span>
        <span>
          {t('controls.pcfLegendHigh')} {maxValue.toFixed(2)}
        </span>
      </div>
      <div
        className="mt-2 h-2 w-full rounded-full"
        style={{
          background:
            'linear-gradient(90deg, #2563eb 0%, #22c55e 45%, #f59e0b 70%, #ef4444 100%)',
        }}
      />
    </div>
  );
}
