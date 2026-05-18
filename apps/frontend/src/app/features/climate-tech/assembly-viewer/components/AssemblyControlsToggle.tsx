import { useTranslation } from '../../../../i18n/useTranslation';
import { cn } from '@/lib/utils';

interface AssemblyControlsToggleProps {
  controlsOpen: boolean;
  onToggle: () => void;
  className?: string;
}

export function AssemblyControlsToggle({
  controlsOpen,
  onToggle,
  className,
}: AssemblyControlsToggleProps) {
  const { t } = useTranslation();

  return (
    <button
      type="button"
      className={cn(
        'rounded-full border border-border/60 bg-slate-950/70 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-100 shadow-lg backdrop-blur',
        className
      )}
      onClick={onToggle}
    >
      {controlsOpen ? t('controls.hideControls') : t('controls.showControls')}
    </button>
  );
}
