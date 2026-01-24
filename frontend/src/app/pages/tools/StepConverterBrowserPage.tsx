import { StepConverterForm } from '@/app/features/tools/step-converter/components/StepConverterForm';
import { StepConverterHeader } from '@/app/features/tools/step-converter/components/StepConverterHeader';
import { StepConverterOutputs } from '@/app/features/tools/step-converter/components/StepConverterOutputs';
import { useStepConverterBrowser } from '@/app/features/tools/step-converter/hooks/useStepConverterBrowser';
import { useTranslation } from '../../i18n/useTranslation';

export function StepConverterBrowserPage() {
  const { t } = useTranslation();
  const converter = useStepConverterBrowser(t);

  return (
    <div className="space-y-8">
      <StepConverterHeader
        t={t}
        badgeKey="tools.stepConverterBrowser.badge"
        titleKey="tools.stepConverterBrowser.title"
        subtitleKey="tools.stepConverterBrowser.subtitle"
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <StepConverterForm t={t} converter={converter} />
        <StepConverterOutputs t={t} converter={converter} />
      </div>
    </div>
  );
}
