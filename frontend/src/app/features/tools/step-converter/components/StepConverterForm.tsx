import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import type {
  ConversionMode,
  StepConverterController,
  TranslateFn,
} from '../types';

type StepConverterFormProps = {
  t: TranslateFn;
  converter: StepConverterController;
};

export function StepConverterForm({ t, converter }: StepConverterFormProps) {
  const {
    file,
    mode,
    linDeflection,
    angDeflection,
    relative,
    parallel,
    status,
    hasInvalidNumbers,
    isAdvanced,
    onFileChange,
    onModeChange,
    onLinDeflectionChange,
    onAngDeflectionChange,
    onRelativeChange,
    onParallelChange,
    onSubmit,
    onReset,
    onCancel,
  } = converter;
  const isBusy = status.state === 'loading';

  const stageLabel =
    status.state === 'loading' && status.stage
      ? t(`tools.stepConverter.status.stage.${status.stage}` as const)
      : t('tools.stepConverter.status.loading');

  return (
    <Card className="border-border/60 bg-background/90">
      <CardHeader>
        <CardTitle>{t('tools.stepConverter.panel.title')}</CardTitle>
        <CardDescription>
          {t('tools.stepConverter.panel.description')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="step-file">
              {t('tools.stepConverter.form.fileLabel')}
            </Label>
            <div className="rounded-xl border border-border/60 bg-background/80 px-4 py-3">
              <input
                id="step-file"
                type="file"
                accept=".step,.stp"
                disabled={isBusy}
                className="block w-full text-sm text-muted-foreground file:mr-4 file:rounded-full file:border-0 file:bg-primary/10 file:px-4 file:py-2 file:text-xs file:font-semibold file:uppercase file:tracking-wide file:text-primary"
                onChange={(event) =>
                  onFileChange(event.target.files?.[0] ?? null)
                }
              />
            </div>
            <p className="text-xs text-muted-foreground">
              {t('tools.stepConverter.form.fileHint')}
            </p>
            {file && (
              <p className="text-xs font-semibold text-foreground">
                {file.name}
              </p>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="mode-select">
                {t('tools.stepConverter.form.modeLabel')}
              </Label>
              <Select
                value={mode}
                onValueChange={(value) => onModeChange(value as ConversionMode)}
                disabled={isBusy}
              >
                <SelectTrigger id="mode-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="basic">
                    {t('tools.stepConverter.form.modeBasic')}
                  </SelectItem>
                  <SelectItem value="advanced">
                    {t('tools.stepConverter.form.modeAdvanced')}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>{t('tools.stepConverter.form.outputLabel')}</Label>
              <div className="rounded-xl border border-border/60 bg-background/80 px-4 py-3 text-sm text-muted-foreground">
                {t('tools.stepConverter.form.outputBundle')}
              </div>
            </div>
          </div>

          {isAdvanced && (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="lin-deflection">
                  {t('tools.stepConverter.form.linDeflection')}
                </Label>
                <input
                  id="lin-deflection"
                  type="number"
                  step="0.01"
                  value={linDeflection}
                  disabled={isBusy}
                  onChange={(event) =>
                    onLinDeflectionChange(event.target.value)
                  }
                  className="w-full rounded-xl border border-border/60 bg-background/80 px-3 py-2 text-sm text-foreground"
                  placeholder="1"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ang-deflection">
                  {t('tools.stepConverter.form.angDeflection')}
                </Label>
                <input
                  id="ang-deflection"
                  type="number"
                  step="0.01"
                  value={angDeflection}
                  disabled={isBusy}
                  onChange={(event) =>
                    onAngDeflectionChange(event.target.value)
                  }
                  className="w-full rounded-xl border border-border/60 bg-background/80 px-3 py-2 text-sm text-foreground"
                  placeholder="0.5"
                />
              </div>
            </div>
          )}

          {isAdvanced && (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex items-center justify-between gap-3 rounded-xl border border-border/60 bg-background/80 px-4 py-3">
                <Label
                  htmlFor="relative-toggle"
                  className="text-sm text-muted-foreground"
                >
                  {t('tools.stepConverter.form.relative')}
                </Label>
                <Switch
                  id="relative-toggle"
                  checked={relative}
                  disabled={isBusy}
                  onCheckedChange={onRelativeChange}
                />
              </div>
              <div className="flex items-center justify-between gap-3 rounded-xl border border-border/60 bg-background/80 px-4 py-3">
                <Label
                  htmlFor="parallel-toggle"
                  className="text-sm text-muted-foreground"
                >
                  {t('tools.stepConverter.form.parallel')}
                </Label>
                <Switch
                  id="parallel-toggle"
                  checked={parallel}
                  disabled={isBusy}
                  onCheckedChange={onParallelChange}
                />
              </div>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={!file || isBusy}>
              {isBusy ? stageLabel : t('tools.stepConverter.form.submit')}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={isBusy ? onCancel : onReset}
            >
              {isBusy
                ? t('tools.stepConverter.form.cancel')
                : t('tools.stepConverter.form.reset')}
            </Button>
            {isAdvanced && hasInvalidNumbers && (
              <span className="text-xs text-destructive">
                {t('tools.stepConverter.status.invalidNumbers')}
              </span>
            )}
          </div>

          <div
            data-testid="step-converter-status"
            data-error-code={
              status.state === 'error' ? status.error.code : undefined
            }
            className={`rounded-xl border px-4 py-3 text-sm ${
              status.state === 'error'
                ? 'border-destructive/50 bg-destructive/10 text-destructive'
                : status.state === 'success'
                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                : 'border-border/60 bg-background/80 text-muted-foreground'
            }`}
          >
            <span className="inline-flex items-center gap-2 font-semibold">
              {status.state === 'loading' && (
                <LoadingSpinner size="xs" className="text-primary" />
              )}
              {status.state === 'idle' && t('tools.stepConverter.status.idle')}
              {status.state === 'loading' && stageLabel}
              {status.state === 'success' &&
                t('tools.stepConverter.status.success')}
              {status.state === 'error' &&
                t('tools.stepConverter.status.error')}
            </span>
            {status.state === 'error' && (
              <span className="ml-2 text-xs text-destructive/80">
                {status.error.message}
              </span>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
