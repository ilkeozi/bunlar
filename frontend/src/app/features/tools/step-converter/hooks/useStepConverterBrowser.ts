import { useEffect, useRef, useState, type FormEvent } from 'react';
import type {
  ConversionMode,
  DownloadLink,
  OutputFormat,
  RequestStatus,
  StepConverterController,
  StepConverterError,
  StepConverterErrorCode,
  StepConverterWorkerStage,
  TranslateFn,
} from '../types';
import { isStepFilename, MAX_BROWSER_STEP_BYTES } from '../utils';

const BASIC_TRIANGULATION = {
  linearDeflection: 1,
  angularDeflection: 0.5,
  relative: false,
  parallel: true,
};

type TriangulatePayload = {
  linearDeflection?: number;
  angularDeflection?: number;
  relative?: boolean;
  parallel?: boolean;
};

type WorkerStartRequest = {
  type: 'START';
  id: number;
  filename: string;
  fileBytes: ArrayBuffer;
  triangulate: TriangulatePayload;
};

type WorkerProgress = {
  type: 'PROGRESS';
  id: number;
  stage: StepConverterWorkerStage;
  progress?: number;
};

type WorkerDone = {
  type: 'DONE';
  id: number;
  bundleName: string;
  bundleBytes: ArrayBuffer;
};

type WorkerFailure = {
  type: 'ERROR';
  id: number;
  error: StepConverterError;
};

type WorkerResponse = WorkerProgress | WorkerDone | WorkerFailure;

function resolveErrorMessage(t: TranslateFn, code: StepConverterErrorCode) {
  const key = `tools.stepConverter.error.${code}` as const;
  return t(key);
}

function validateBrowserFile(
  t: TranslateFn,
  file: File
): StepConverterError | null {
  if (!isStepFilename(file.name)) {
    return {
      code: 'UNSUPPORTED_EXTENSION',
      message: resolveErrorMessage(t, 'UNSUPPORTED_EXTENSION'),
      detail: { filename: file.name },
    };
  }
  if (file.size > MAX_BROWSER_STEP_BYTES) {
    return {
      code: 'FILE_TOO_LARGE',
      message: resolveErrorMessage(t, 'FILE_TOO_LARGE'),
      detail: { size: file.size, max: MAX_BROWSER_STEP_BYTES },
    };
  }
  return null;
}

function errorStatus(error: StepConverterError): RequestStatus {
  return { state: 'error', error };
}

function createZipDownload(bundle: WorkerDone): DownloadLink {
  const blob = new Blob([bundle.bundleBytes], { type: 'application/zip' });
  return {
    url: URL.createObjectURL(blob),
    name: bundle.bundleName,
  };
}

export function useStepConverterBrowser(
  t: TranslateFn
): StepConverterController {
  const workerRef = useRef<Worker | null>(null);
  const workerRequestIdRef = useRef(0);
  const requestIdRef = useRef(0);

  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<ConversionMode>('basic');
  const [format] = useState<OutputFormat>('glb');
  const [linDeflection, setLinDeflection] = useState('1');
  const [angDeflection, setAngDeflection] = useState('0.5');
  const [relative, setRelative] = useState(false);
  const [parallel, setParallel] = useState(true);
  const [includeBom] = useState(false);
  const [includeNodeMap] = useState(false);
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

  const clearDownloads = () => {
    revokeDownload(download);
    revokeDownload(bom);
    revokeDownload(nodeMap);
    setDownload(null);
    setBom(null);
    setNodeMap(null);
  };

  const ensureWorker = () => {
    if (!workerRef.current) {
      workerRef.current = new Worker(
        new URL('../workers/stepConverter.worker.ts', import.meta.url),
        { type: 'module' }
      );
    }
    return workerRef.current;
  };

  const terminateWorker = () => {
    if (workerRef.current) {
      workerRef.current.terminate();
      workerRef.current = null;
    }
  };

  const runWorkerConversion = (params: {
    filename: string;
    fileBytes: ArrayBuffer;
    triangulate: TriangulatePayload;
  }) => {
    const worker = ensureWorker();
    const id = workerRequestIdRef.current + 1;
    workerRequestIdRef.current = id;

    return new Promise<WorkerDone>((resolve, reject) => {
      const handleMessage = (event: MessageEvent<WorkerResponse>) => {
        if (!event.data || event.data.id !== id) return;
        if (event.data.type === 'PROGRESS') {
          setStatus({ state: 'loading', stage: event.data.stage });
          return;
        }
        cleanup();
        if (event.data.type === 'DONE') {
          resolve(event.data);
          return;
        }
        reject(event.data.error);
      };

      const handleError = (event: ErrorEvent) => {
        cleanup();
        reject({
          code: 'CONVERSION_FAILED',
          message: event.message || resolveErrorMessage(t, 'CONVERSION_FAILED'),
        } satisfies StepConverterError);
      };

      const cleanup = () => {
        worker.removeEventListener('message', handleMessage);
        worker.removeEventListener('error', handleError);
      };

      worker.addEventListener('message', handleMessage);
      worker.addEventListener('error', handleError);

      const payload: WorkerStartRequest = {
        type: 'START',
        id,
        filename: params.filename,
        fileBytes: params.fileBytes,
        triangulate: params.triangulate,
      };
      worker.postMessage(payload, [params.fileBytes]);
    });
  };

  useEffect(() => {
    return () => {
      revokeDownload(download);
      revokeDownload(bom);
      revokeDownload(nodeMap);
      terminateWorker();
    };
  }, [download, bom, nodeMap]);

  const onFileChange = (next: File | null) => {
    requestIdRef.current += 1;
    clearDownloads();
    terminateWorker();
    setMetadataStatus({ state: 'idle' });
    setBom(null);
    setNodeMap(null);

    setFile(next);
    if (!next) {
      setStatus({ state: 'idle' });
      return;
    }

    const invalid = validateBrowserFile(t, next);
    if (invalid) {
      setStatus(errorStatus(invalid));
      return;
    }

    setStatus({ state: 'idle' });
  };

  const onReset = () => {
    requestIdRef.current += 1;
    setFile(null);
    setMode('basic');
    setLinDeflection('');
    setAngDeflection('');
    setRelative(false);
    setParallel(false);
    setStatus({ state: 'idle' });
    setMetadataStatus({ state: 'idle' });
    clearDownloads();
    terminateWorker();
  };

  const onCancel = () => {
    requestIdRef.current += 1;
    setStatus({ state: 'idle' });
    setMetadataStatus({ state: 'idle' });
    clearDownloads();
    terminateWorker();
  };

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) {
      setStatus(
        errorStatus({
          code: 'CONVERSION_FAILED',
          message: t('tools.stepConverter.status.missingFile'),
        })
      );
      return;
    }
    if (isAdvanced && hasInvalidNumbers) {
      setStatus(
        errorStatus({
          code: 'CONVERSION_FAILED',
          message: t('tools.stepConverter.status.invalidNumbers'),
        })
      );
      return;
    }

    const fileError = validateBrowserFile(t, file);
    if (fileError) {
      setStatus(errorStatus(fileError));
      return;
    }

    setStatus({ state: 'loading', stage: 'parsing' });
    setMetadataStatus({ state: 'idle' });
    clearDownloads();

    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;

    try {
      const inputBuffer = await file.arrayBuffer();
      if (requestIdRef.current !== requestId) return;

      const triangulateOptions = isAdvanced
        ? {
            linearDeflection: linNumber,
            angularDeflection: angNumber,
            relative,
            parallel,
          }
        : BASIC_TRIANGULATION;

      const result = await runWorkerConversion({
        filename: file.name,
        fileBytes: inputBuffer,
        triangulate: triangulateOptions,
      });
      if (requestIdRef.current !== requestId) return;

      setDownload(createZipDownload(result));
      setStatus({ state: 'success' });
    } catch (error) {
      if (requestIdRef.current !== requestId) return;

      const err = error as Partial<StepConverterError>;
      const code = (err.code ?? 'CONVERSION_FAILED') as StepConverterErrorCode;
      setStatus(
        errorStatus({
          code,
          message:
            resolveErrorMessage(t, code) ||
            err.message ||
            t('tools.stepConverter.status.error'),
          detail: err.detail,
        })
      );
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
    onFileChange,
    onModeChange: setMode,
    onFormatChange: () => {
      // Browser converter always outputs a bundle zip containing a GLB.
    },
    onLinDeflectionChange: setLinDeflection,
    onAngDeflectionChange: setAngDeflection,
    onRelativeChange: setRelative,
    onParallelChange: setParallel,
    onIncludeBomChange: () => {
      // Browser converter always embeds metadata in the bundle.
    },
    onIncludeNodeMapChange: () => {
      // Browser converter always embeds metadata in the bundle.
    },
    onSubmit,
    onReset,
    onCancel,
  };
}
