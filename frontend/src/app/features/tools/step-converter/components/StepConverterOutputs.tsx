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
  const { download, status, conversionWarnings, meshStats } = converter;
  const showWarnings =
    Boolean(download) &&
    status.state === 'success' &&
    conversionWarnings.length > 0;

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

      {showWarnings && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardHeader>
            <CardTitle>
              {t('tools.stepConverter.output.warnings.title')}
            </CardTitle>
            <CardDescription>
              {t('tools.stepConverter.output.warnings.description')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {meshStats && (
              <div className="text-xs text-amber-100/80">
                {t('tools.stepConverter.output.meshStats.triangles')}:{' '}
                {meshStats.triangles.toLocaleString()} |{' '}
                {t('tools.stepConverter.output.meshStats.primitives')}:{' '}
                {meshStats.primitiveCount.toLocaleString()} |{' '}
                {t('tools.stepConverter.output.meshStats.nodes')}:{' '}
                {meshStats.nodeCount.toLocaleString()}
              </div>
            )}
            <ul className="list-disc space-y-1 pl-4 text-sm text-amber-50">
              {conversionWarnings.map((warning, index) => (
                <li key={`${warning.code}-${index}`}>{warning.message}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
