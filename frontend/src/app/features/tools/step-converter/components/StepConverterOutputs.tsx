import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import type { StepConverterController, TranslateFn } from '../types';

type StepConverterOutputsProps = {
  t: TranslateFn;
  converter: StepConverterController;
};

export function StepConverterOutputs({
  t,
  converter,
}: StepConverterOutputsProps) {
  const { download, bom, nodeMap, metadataStatus } = converter;
  const showMetadata = Boolean(
    bom || nodeMap || metadataStatus.state !== 'idle'
  );

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

      {showMetadata && (
        <Card className="border-border/60 bg-background/90">
          <CardHeader>
            <CardTitle>
              {t('tools.stepConverter.output.metadataLabel')}
            </CardTitle>
            {metadataStatus.state !== 'idle' && (
              <CardDescription className="flex items-center gap-2">
                {metadataStatus.state === 'loading' && (
                  <LoadingSpinner size="xs" className="text-primary" />
                )}
                <span>
                  {metadataStatus.state === 'loading' &&
                    t('tools.stepConverter.status.metadataLoading')}
                  {metadataStatus.state === 'success' &&
                    t('tools.stepConverter.status.metadataSuccess')}
                  {metadataStatus.state === 'error' &&
                    t('tools.stepConverter.status.metadataError')}
                </span>
              </CardDescription>
            )}
          </CardHeader>
          <CardContent className="space-y-3">
            {bom && (
              <a
                href={bom.url}
                download={bom.name}
                className="block text-xs font-semibold uppercase tracking-wide text-emerald-200"
              >
                {t('tools.stepConverter.output.bomCta')}
              </a>
            )}
            {nodeMap && (
              <a
                href={nodeMap.url}
                download={nodeMap.name}
                className="block text-xs font-semibold uppercase tracking-wide text-emerald-200"
              >
                {t('tools.stepConverter.output.nodeMapCta')}
              </a>
            )}
            {metadataStatus.state === 'error' && metadataStatus.message && (
              <p className="text-xs text-destructive">
                {metadataStatus.message}
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
