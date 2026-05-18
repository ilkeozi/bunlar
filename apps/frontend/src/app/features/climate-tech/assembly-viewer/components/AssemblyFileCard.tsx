import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { useTranslation } from '../../../../i18n/useTranslation';

type AssemblyFileStatus = 'idle' | 'converting' | 'loading' | 'ready' | 'error';

type AssemblyFileCardProps = {
  fileName: string;
  status: AssemblyFileStatus;
  error: string | null;
  isSample: boolean;
  onFileChange: (file: File | null) => void;
  onUseSample: () => void;
};

export function AssemblyFileCard({
  fileName,
  status,
  error,
  isSample,
  onFileChange,
  onUseSample,
}: AssemblyFileCardProps) {
  const { t } = useTranslation();
  const hintId = 'assembly-file-hint';
  const statusLabel = (() => {
    switch (status) {
      case 'converting':
        return t('assemblyViewer.status.converting');
      case 'loading':
        return t('assemblyViewer.status.loading');
      case 'ready':
        return t('assemblyViewer.status.ready');
      case 'error':
        return t('assemblyViewer.status.error');
      default:
        return t('assemblyViewer.status.idle');
    }
  })();

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('assemblyViewer.input.title')}</CardTitle>
        <CardDescription>{t('assemblyViewer.input.description')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-2">
          <Label htmlFor="assembly-file-input">
            {t('assemblyViewer.input.label')}
          </Label>
          <input
            id="assembly-file-input"
            name="assembly-file-input"
            type="file"
            autoComplete="off"
            accept=".step,.stp,.iges,.igs"
            aria-describedby={hintId}
            className="flex w-full cursor-pointer rounded-md border border-border/60 bg-background/60 px-3 py-2 text-xs text-foreground file:mr-3 file:rounded-full file:border-0 file:bg-primary/10 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-primary hover:file:bg-primary/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/70 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
          />
          <p id={hintId} className="text-xs text-muted-foreground">
            {t('assemblyViewer.input.hint')}
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-background/40 px-3 py-2 text-xs text-muted-foreground">
          <span className="text-foreground/80">{fileName}</span>
          <span
            role="status"
            aria-live="polite"
            className={status === 'error' ? 'text-destructive' : ''}
          >
            {statusLabel}
          </span>
        </div>
        {error && (
          <p className="text-xs text-destructive" role="alert">
            {error}
          </p>
        )}

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onUseSample}
          disabled={isSample}
          className="w-full justify-center"
        >
          {t('assemblyViewer.input.sample')}
        </Button>
      </CardContent>
    </Card>
  );
}
