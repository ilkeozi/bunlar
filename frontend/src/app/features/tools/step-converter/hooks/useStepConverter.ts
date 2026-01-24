import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import type {
  ConversionMode,
  DownloadLink,
  OutputFormat,
  RequestStatus,
  StepConverterController,
  TranslateFn,
} from '../types';
import {
  buildMetadataName,
  createJsonDownload,
  fetchMetadata,
  resolveApiBase,
  resolveDownloadName,
} from '../utils';

export type { StepConverterController };

const HEALTH_TIMEOUT_MS = 3000;
const REQUEST_TIMEOUT_MS = 60_000;
const BASIC_TRIANGULATION = {
  linearDeflection: 1,
  angularDeflection: 0.5,
  relative: false,
  parallel: true,
};

export function useStepConverter(t: TranslateFn): StepConverterController {
  const apiBase = useMemo(resolveApiBase, []);
  const endpoint = useMemo(() => `${apiBase}/convert/upload`, [apiBase]);
  const metadataEndpoint = useMemo(
    () => `${apiBase}/convert/metadata/upload`,
    [apiBase]
  );

  const requestIdRef = useRef(0);
  const abortRef = useRef<AbortController | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<ConversionMode>('basic');
  const [format, setFormat] = useState<OutputFormat>('glb');
  const [linDeflection, setLinDeflection] = useState('1');
  const [angDeflection, setAngDeflection] = useState('0.5');
  const [relative, setRelative] = useState(false);
  const [parallel, setParallel] = useState(true);
  const [includeBom, setIncludeBom] = useState(false);
  const [includeNodeMap, setIncludeNodeMap] = useState(false);
  const [status, setStatus] = useState<RequestStatus>({ state: 'idle' });
  const [metadataStatus, setMetadataStatus] = useState<RequestStatus>({
    state: 'idle',
  });
  const [download, setDownload] = useState<DownloadLink | null>(null);
  const [bom, setBom] = useState<DownloadLink | null>(null);
  const [nodeMap, setNodeMap] = useState<DownloadLink | null>(null);

  const linNumber =
    linDeflection.trim() === '' ? undefined : Number(linDeflection);
  const angNumber =
    angDeflection.trim() === '' ? undefined : Number(angDeflection);
  const hasInvalidNumbers =
    (linNumber !== undefined && Number.isNaN(linNumber)) ||
    (angNumber !== undefined && Number.isNaN(angNumber));
  const isAdvanced = mode === 'advanced';

  const revokeDownload = (link: DownloadLink | null) => {
    if (link) {
      URL.revokeObjectURL(link.url);
    }
  };

  const withTimeout = async <T,>(
    promise: Promise<T>,
    timeoutMs: number,
    onTimeout?: () => void
  ) => {
    let timeoutId: number | null = null;
    const timeoutPromise = new Promise<never>((_resolve, reject) => {
      timeoutId = window.setTimeout(() => {
        if (onTimeout) {
          onTimeout();
        }
        const error = new Error('Request timed out.');
        error.name = 'TimeoutError';
        reject(error);
      }, timeoutMs);
    });

    try {
      return await Promise.race([promise, timeoutPromise]);
    } finally {
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
    }
  };

  const checkApiAvailability = async () => {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(
      () => controller.abort(),
      HEALTH_TIMEOUT_MS
    );
    try {
      const response = await fetch(`${apiBase}/health`, {
        signal: controller.signal,
      });
      return response.ok;
    } catch {
      return false;
    } finally {
      window.clearTimeout(timeoutId);
    }
  };

  const clearDownloads = () => {
    revokeDownload(download);
    revokeDownload(bom);
    revokeDownload(nodeMap);
    setDownload(null);
    setBom(null);
    setNodeMap(null);
  };

  useEffect(() => {
    return () => {
      revokeDownload(download);
      revokeDownload(bom);
      revokeDownload(nodeMap);
      abortRef.current?.abort();
    };
  }, [download, bom, nodeMap]);

  const onReset = () => {
    requestIdRef.current += 1;
    abortRef.current?.abort();
    abortRef.current = null;
    setFile(null);
    setMode('basic');
    setFormat('glb');
    setLinDeflection('');
    setAngDeflection('');
    setRelative(false);
    setParallel(false);
    setIncludeBom(false);
    setIncludeNodeMap(false);
    setStatus({ state: 'idle' });
    setMetadataStatus({ state: 'idle' });
    clearDownloads();
  };

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) {
      setStatus({
        state: 'error',
        message: t('tools.stepConverter.status.missingFile'),
      });
      return;
    }
    if (isAdvanced && hasInvalidNumbers) {
      setStatus({
        state: 'error',
        message: t('tools.stepConverter.status.invalidNumbers'),
      });
      return;
    }

    setStatus({ state: 'loading' });
    setMetadataStatus({ state: 'idle' });
    clearDownloads();

    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    abortRef.current?.abort();
    abortRef.current = null;

    const apiOk = await checkApiAvailability();
    if (requestIdRef.current !== requestId) {
      return;
    }
    if (!apiOk) {
      setStatus({
        state: 'error',
        message: t('tools.stepConverter.status.apiUnavailable'),
      });
      return;
    }

    const guardTimeoutId = window.setTimeout(() => {
      if (requestIdRef.current !== requestId) {
        return;
      }
      requestIdRef.current += 1;
      abortRef.current?.abort();
      abortRef.current = null;
      setStatus({
        state: 'error',
        message: t('tools.stepConverter.status.timeout'),
      });
    }, REQUEST_TIMEOUT_MS);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', format);
    if (isAdvanced) {
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
    } else {
      formData.append(
        'linDeflection',
        String(BASIC_TRIANGULATION.linearDeflection)
      );
      formData.append(
        'angDeflection',
        String(BASIC_TRIANGULATION.angularDeflection)
      );
      if (BASIC_TRIANGULATION.relative) {
        formData.append('relative', 'true');
      }
      if (BASIC_TRIANGULATION.parallel) {
        formData.append('parallel', 'true');
      }
    }

    try {
      const controller = new AbortController();
      abortRef.current = controller;
      const response = await withTimeout(
        fetch(endpoint, {
          method: 'POST',
          body: formData,
          signal: controller.signal,
        }),
        REQUEST_TIMEOUT_MS,
        () => controller.abort()
      );

      if (requestIdRef.current !== requestId) {
        return;
      }
      if (!response.ok) {
        const errorText = await response.text();
        setStatus({
          state: 'error',
          message: errorText || t('tools.stepConverter.status.error'),
        });
        return;
      }

      const blob = await withTimeout(
        response.blob(),
        REQUEST_TIMEOUT_MS,
        () => controller.abort()
      );
      if (requestIdRef.current !== requestId) {
        return;
      }
      const objectUrl = URL.createObjectURL(blob);
      const outputName = resolveDownloadName(
        response.headers.get('content-disposition'),
        file.name,
        format
      );
      setDownload({ url: objectUrl, name: outputName });
      setStatus({ state: 'success' });

      if (isAdvanced && (includeBom || includeNodeMap)) {
        setMetadataStatus({ state: 'loading' });
        const metadata = await fetchMetadata(
          metadataEndpoint,
          file,
          includeBom,
          includeNodeMap
        );
        if (requestIdRef.current !== requestId) {
          return;
        }
        if (!metadata.ok) {
          setMetadataStatus({
            state: 'error',
            message:
              metadata.error ?? t('tools.stepConverter.status.metadataError'),
          });
          return;
        }
        if (metadata.bom) {
          setBom(
            createJsonDownload(
              metadata.bom,
              buildMetadataName(file.name, 'bom')
            )
          );
        }
        if (metadata.nodeMap) {
          setNodeMap(
            createJsonDownload(
              metadata.nodeMap,
              buildMetadataName(file.name, 'node-map')
            )
          );
        }
        setMetadataStatus({ state: 'success' });
      }
    } catch (error) {
      if (requestIdRef.current !== requestId) {
        return;
      }
      if (
        (error instanceof DOMException && error.name === 'AbortError') ||
        (error instanceof Error && error.name === 'TimeoutError')
      ) {
        setStatus({
          state: 'error',
          message: t('tools.stepConverter.status.timeout'),
        });
        return;
      }
      setStatus({
        state: 'error',
        message:
          error instanceof Error
            ? error.message
            : t('tools.stepConverter.status.error'),
      });
    } finally {
      window.clearTimeout(guardTimeoutId);
    }
    if (abortRef.current) {
      abortRef.current = null;
    }
  };

  return {
    file,
    mode,
    format,
    linDeflection,
    angDeflection,
    relative,
    parallel,
    includeBom,
    includeNodeMap,
    status,
    metadataStatus,
    download,
    bom,
    nodeMap,
    hasInvalidNumbers,
    isAdvanced,
    onFileChange: setFile,
    onModeChange: setMode,
    onFormatChange: setFormat,
    onLinDeflectionChange: setLinDeflection,
    onAngDeflectionChange: setAngDeflection,
    onRelativeChange: setRelative,
    onParallelChange: setParallel,
    onIncludeBomChange: setIncludeBom,
    onIncludeNodeMapChange: setIncludeNodeMap,
    onSubmit,
    onReset,
  };
}
