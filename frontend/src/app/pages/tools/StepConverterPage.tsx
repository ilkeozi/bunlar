import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { useTranslation } from '../../i18n/useTranslation';

type OutputFormat = 'gltf' | 'glb' | 'obj';

const FORMAT_OPTIONS: Array<{ value: OutputFormat; label: string }> = [
  { value: 'gltf', label: 'glTF' },
  { value: 'glb', label: 'GLB' },
  { value: 'obj', label: 'OBJ' },
];

function resolveApiBase() {
  const raw = import.meta.env.VITE_OCCT_API_URL as string | undefined;
  const base = raw && raw.trim().length > 0 ? raw : 'http://localhost:3001';
  return base.replace(/\/$/, '');
}

export function StepConverterPage() {
  const { t } = useTranslation();
  const apiBase = resolveApiBase();
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState<OutputFormat>('gltf');
  const [linDeflection, setLinDeflection] = useState('1');
  const [angDeflection, setAngDeflection] = useState('0.5');
  const [relative, setRelative] = useState(false);
  const [parallel, setParallel] = useState(true);
  const [includeBom, setIncludeBom] = useState(false);
  const [includeNodeMap, setIncludeNodeMap] = useState(false);
  const [status, setStatus] = useState<{ state: 'idle' | 'loading' | 'success' | 'error'; message?: string }>({
    state: 'idle',
  });
  const [metadataStatus, setMetadataStatus] = useState<{
    state: 'idle' | 'loading' | 'success' | 'error';
    message?: string;
  }>({ state: 'idle' });
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [downloadName, setDownloadName] = useState<string | null>(null);
  const [bomUrl, setBomUrl] = useState<string | null>(null);
  const [bomName, setBomName] = useState<string | null>(null);
  const [nodeMapUrl, setNodeMapUrl] = useState<string | null>(null);
  const [nodeMapName, setNodeMapName] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (downloadUrl) {
        URL.revokeObjectURL(downloadUrl);
      }
      if (bomUrl) {
        URL.revokeObjectURL(bomUrl);
      }
      if (nodeMapUrl) {
        URL.revokeObjectURL(nodeMapUrl);
      }
    };
  }, [downloadUrl, bomUrl, nodeMapUrl]);

  const endpoint = useMemo(() => {
    return `${apiBase}/convert/upload`;
  }, [apiBase]);

  const metadataEndpoint = useMemo(() => {
    return `${apiBase}/convert/metadata/upload`;
  }, [apiBase]);

  const linNumber = linDeflection.trim() === '' ? undefined : Number(linDeflection);
  const angNumber = angDeflection.trim() === '' ? undefined : Number(angDeflection);
  const hasInvalidNumbers =
    (linNumber !== undefined && Number.isNaN(linNumber)) ||
    (angNumber !== undefined && Number.isNaN(angNumber));

  const fileLabel = file ? file.name : t('tools.stepConverter.form.filePlaceholder');

  const reset = () => {
    setFile(null);
    setLinDeflection('');
    setAngDeflection('');
    setRelative(false);
    setParallel(false);
    setIncludeBom(false);
    setIncludeNodeMap(false);
    setStatus({ state: 'idle' });
    setMetadataStatus({ state: 'idle' });
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl);
      setDownloadUrl(null);
      setDownloadName(null);
    }
    if (bomUrl) {
      URL.revokeObjectURL(bomUrl);
      setBomUrl(null);
      setBomName(null);
    }
    if (nodeMapUrl) {
      URL.revokeObjectURL(nodeMapUrl);
      setNodeMapUrl(null);
      setNodeMapName(null);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) {
      setStatus({ state: 'error', message: t('tools.stepConverter.status.missingFile') });
      return;
    }
    if (hasInvalidNumbers) {
      setStatus({ state: 'error', message: t('tools.stepConverter.status.invalidNumbers') });
      return;
    }

    setStatus({ state: 'loading' });
    setMetadataStatus({ state: 'idle' });
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl);
      setDownloadUrl(null);
      setDownloadName(null);
    }
    if (bomUrl) {
      URL.revokeObjectURL(bomUrl);
      setBomUrl(null);
      setBomName(null);
    }
    if (nodeMapUrl) {
      URL.revokeObjectURL(nodeMapUrl);
      setNodeMapUrl(null);
      setNodeMapName(null);
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', format);
    if (linNumber !== undefined) {
      formData.append('linDeflection', String(linNumber));
    }
    if (angNumber !== undefined) {
      formData.append('angDeflection', String(angNumber));
    }
    if (relative) {
      formData.append('relative', 'true');
    }
    if (parallel) {
      formData.append('parallel', 'true');
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        setStatus({
          state: 'error',
          message: errorText || t('tools.stepConverter.status.error'),
        });
        return;
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const outputName = resolveDownloadName(response.headers.get('content-disposition'), file.name, format);
      setDownloadUrl(objectUrl);
      setDownloadName(outputName);
      setStatus({ state: 'success' });

      if (includeBom || includeNodeMap) {
        setMetadataStatus({ state: 'loading' });
        const metadata = await fetchMetadata(metadataEndpoint, file, includeBom, includeNodeMap);
        if (!metadata.ok) {
          setMetadataStatus({
            state: 'error',
            message: metadata.error ?? t('tools.stepConverter.status.metadataError'),
          });
          return;
        }
        if (metadata.bom) {
          const { url, name } = createJsonDownload(metadata.bom, buildMetadataName(file.name, 'bom'));
          setBomUrl(url);
          setBomName(name);
        }
        if (metadata.nodeMap) {
          const { url, name } = createJsonDownload(
            metadata.nodeMap,
            buildMetadataName(file.name, 'node-map')
          );
          setNodeMapUrl(url);
          setNodeMapName(name);
        }
        setMetadataStatus({ state: 'success' });
      }
    } catch (error) {
      setStatus({
        state: 'error',
        message: error instanceof Error ? error.message : t('tools.stepConverter.status.error'),
      });
    }
  };

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="border-border/60 text-[11px] uppercase tracking-wide">
            {t('subjects.tools.title')}
          </Badge>
          <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t('tools.stepConverter.badge')}
          </span>
        </div>
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          {t('tools.stepConverter.title')}
        </h2>
        <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
          {t('tools.stepConverter.subtitle')}
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <Card className="border-border/60 bg-background/90">
          <CardHeader>
            <CardTitle>{t('tools.stepConverter.panel.title')}</CardTitle>
            <CardDescription>{t('tools.stepConverter.panel.description')}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="step-file">{t('tools.stepConverter.form.fileLabel')}</Label>
                <div className="rounded-xl border border-border/60 bg-background/80 px-4 py-3">
                  <input
                    id="step-file"
                    type="file"
                    accept=".step,.stp,.iges,.igs"
                    className="block w-full text-sm text-muted-foreground file:mr-4 file:rounded-full file:border-0 file:bg-primary/10 file:px-4 file:py-2 file:text-xs file:font-semibold file:uppercase file:tracking-wide file:text-primary"
                    onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  {t('tools.stepConverter.form.fileHint')}
                </p>
                <p
                  className={`text-xs ${file ? 'font-semibold text-foreground' : 'text-muted-foreground'}`}
                >
                  {fileLabel}
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="format-select">{t('tools.stepConverter.form.formatLabel')}</Label>
                  <Select value={format} onValueChange={(value) => setFormat(value as OutputFormat)}>
                    <SelectTrigger id="format-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {FORMAT_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lin-deflection">{t('tools.stepConverter.form.linDeflection')}</Label>
                  <input
                    id="lin-deflection"
                    type="number"
                    step="0.01"
                    value={linDeflection}
                    onChange={(event) => setLinDeflection(event.target.value)}
                    className="w-full rounded-xl border border-border/60 bg-background/80 px-3 py-2 text-sm text-foreground"
                    placeholder="1"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ang-deflection">{t('tools.stepConverter.form.angDeflection')}</Label>
                  <input
                    id="ang-deflection"
                    type="number"
                    step="0.01"
                    value={angDeflection}
                    onChange={(event) => setAngDeflection(event.target.value)}
                    className="w-full rounded-xl border border-border/60 bg-background/80 px-3 py-2 text-sm text-foreground"
                    placeholder="0.5"
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex items-center justify-between gap-3 rounded-xl border border-border/60 bg-background/80 px-4 py-3">
                  <Label htmlFor="relative-toggle" className="text-sm text-muted-foreground">
                    {t('tools.stepConverter.form.relative')}
                  </Label>
                  <Switch id="relative-toggle" checked={relative} onCheckedChange={setRelative} />
                </div>
                <div className="flex items-center justify-between gap-3 rounded-xl border border-border/60 bg-background/80 px-4 py-3">
                  <Label htmlFor="parallel-toggle" className="text-sm text-muted-foreground">
                    {t('tools.stepConverter.form.parallel')}
                  </Label>
                  <Switch id="parallel-toggle" checked={parallel} onCheckedChange={setParallel} />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex items-center justify-between gap-3 rounded-xl border border-border/60 bg-background/80 px-4 py-3">
                  <Label htmlFor="bom-toggle" className="text-sm text-muted-foreground">
                    {t('tools.stepConverter.form.includeBom')}
                  </Label>
                  <Switch id="bom-toggle" checked={includeBom} onCheckedChange={setIncludeBom} />
                </div>
                <div className="flex items-center justify-between gap-3 rounded-xl border border-border/60 bg-background/80 px-4 py-3">
                  <Label htmlFor="node-map-toggle" className="text-sm text-muted-foreground">
                    {t('tools.stepConverter.form.includeNodeMap')}
                  </Label>
                  <Switch
                    id="node-map-toggle"
                    checked={includeNodeMap}
                    onCheckedChange={setIncludeNodeMap}
                  />
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Button type="submit" disabled={!file || status.state === 'loading'}>
                  {status.state === 'loading'
                    ? t('tools.stepConverter.status.loading')
                    : t('tools.stepConverter.form.submit')}
                </Button>
                <Button type="button" variant="outline" onClick={reset}>
                  {t('tools.stepConverter.form.reset')}
                </Button>
                {hasInvalidNumbers && (
                  <span className="text-xs text-destructive">
                    {t('tools.stepConverter.status.invalidNumbers')}
                  </span>
                )}
              </div>

              <div
                className={`rounded-xl border px-4 py-3 text-sm ${
                  status.state === 'error'
                    ? 'border-destructive/50 bg-destructive/10 text-destructive'
                    : status.state === 'success'
                      ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                      : 'border-border/60 bg-background/80 text-muted-foreground'
                }`}
              >
                <span className="font-semibold">
                  {status.state === 'idle' && t('tools.stepConverter.status.idle')}
                  {status.state === 'loading' && t('tools.stepConverter.status.loading')}
                  {status.state === 'success' && t('tools.stepConverter.status.success')}
                  {status.state === 'error' && t('tools.stepConverter.status.error')}
                </span>
                {status.message && status.state === 'error' && (
                  <span className="ml-2 text-xs text-destructive/80">{status.message}</span>
                )}
              </div>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="border-border/60 bg-background/90">
            <CardHeader>
              <CardTitle>{t('tools.stepConverter.notes.title')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>{t('tools.stepConverter.notes.item1')}</p>
              <p>{t('tools.stepConverter.notes.item2')}</p>
              <p>{t('tools.stepConverter.notes.item3')}</p>
            </CardContent>
          </Card>

          {downloadUrl && downloadName && (
            <Card className="border-emerald-500/30 bg-emerald-500/5">
              <CardHeader>
                <CardTitle>{t('tools.stepConverter.output.label')}</CardTitle>
                <CardDescription>{downloadName}</CardDescription>
              </CardHeader>
              <CardContent>
                <a
                  href={downloadUrl}
                  download={downloadName}
                  className="text-xs font-semibold uppercase tracking-wide text-emerald-200"
                >
                  {t('tools.stepConverter.output.cta')}
                </a>
              </CardContent>
            </Card>
          )}

          {(bomUrl || nodeMapUrl || metadataStatus.state !== 'idle') && (
            <Card className="border-border/60 bg-background/90">
              <CardHeader>
                <CardTitle>{t('tools.stepConverter.output.metadataLabel')}</CardTitle>
                {metadataStatus.state !== 'idle' && (
                  <CardDescription>
                    {metadataStatus.state === 'loading' && t('tools.stepConverter.status.metadataLoading')}
                    {metadataStatus.state === 'success' && t('tools.stepConverter.status.metadataSuccess')}
                    {metadataStatus.state === 'error' && t('tools.stepConverter.status.metadataError')}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-3">
                {bomUrl && bomName && (
                  <a
                    href={bomUrl}
                    download={bomName}
                    className="block text-xs font-semibold uppercase tracking-wide text-emerald-200"
                  >
                    {t('tools.stepConverter.output.bomCta')}
                  </a>
                )}
                {nodeMapUrl && nodeMapName && (
                  <a
                    href={nodeMapUrl}
                    download={nodeMapName}
                    className="block text-xs font-semibold uppercase tracking-wide text-emerald-200"
                  >
                    {t('tools.stepConverter.output.nodeMapCta')}
                  </a>
                )}
                {metadataStatus.state === 'error' && metadataStatus.message && (
                  <p className="text-xs text-destructive">{metadataStatus.message}</p>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function resolveDownloadName(
  contentDisposition: string | null,
  sourceName: string,
  format: OutputFormat
) {
  if (contentDisposition) {
    const match = /filename="([^"]+)"/.exec(contentDisposition);
    if (match?.[1]) {
      return match[1];
    }
  }
  const baseName = sourceName.replace(/\.[^/.]+$/, '');
  return `${baseName}.${format}`;
}

async function fetchMetadata(
  endpoint: string,
  file: File,
  includeBom: boolean,
  includeNodeMap: boolean
) {
  const formData = new FormData();
  formData.append('file', file);
  if (includeBom) {
    formData.append('includeBom', 'true');
  }
  if (includeNodeMap) {
    formData.append('includeNodeMap', 'true');
  }

  try {
    const response = await fetch(endpoint, { method: 'POST', body: formData });
    if (!response.ok) {
      const errorText = await response.text();
      return { ok: false, error: errorText };
    }
    const payload = (await response.json()) as {
      ok: boolean;
      bom?: unknown;
      nodeMap?: unknown;
      error?: string;
    };
    if (!payload.ok) {
      return { ok: false, error: payload.error };
    }
    return { ok: true, bom: payload.bom, nodeMap: payload.nodeMap };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : 'Request failed.' };
  }
}

function createJsonDownload(payload: unknown, name: string) {
  const json = JSON.stringify(payload, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  return { url, name };
}

function buildMetadataName(sourceName: string, suffix: 'bom' | 'node-map') {
  const baseName = sourceName.replace(/\.[^/.]+$/, '');
  return `${baseName}.${suffix}.json`;
}
