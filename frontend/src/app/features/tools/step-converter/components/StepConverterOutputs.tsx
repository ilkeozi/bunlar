import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import type { StepConverterController, TranslateFn } from '../types';

type StepConverterOutputsProps = {
  t: TranslateFn;
  converter: StepConverterController;
};

export function StepConverterOutputs({
  t,
  converter,
}: StepConverterOutputsProps) {
  const { download } = converter;

  return (
    <div className="space-y-6">
      {download && (
        <Card className="border-emerald-500/30 bg-emerald-500/5">
          <CardHeader>
            <CardTitle>{t('tools.stepConverter.output.label')}</CardTitle>
            <CardDescription>{download.name}</CardDescription>
          </CardHeader>
          <CardContent>
            <a
              href={download.url}
              download={download.name}
              className="text-xs font-semibold uppercase tracking-wide text-emerald-200"
            >
              {t('tools.stepConverter.output.cta')}
            </a>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
