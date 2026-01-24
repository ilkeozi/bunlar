import { useEffect, useRef, useState, type FormEvent } from 'react';
import type { InputFormat } from 'opencascade-convert/browser';
import type {
  ConversionMode,
  DownloadLink,
  OutputFormat,
  RequestStatus,
  StepConverterController,
  TranslateFn,
} from '../types';
import { buildMetadataName, createJsonDownload } from '../utils';

const BASIC_TRIANGULATION = {
  linearDeflection: 1,
  angularDeflection: 0.5,
  relative: false,
  parallel: true,
};

type WorkerSuccess =
  | {
      ok: true;
      outputFormat: 'glb' | 'obj';
      data: ArrayBuffer;
      bom?: unknown;
      nodeMap?: unknown;
    }
  | {
      ok: true;
      outputFormat: 'gltf';
      gltf: ArrayBuffer;
      bin: ArrayBuffer;
      bom?: unknown;
      nodeMap?: unknown;
    };

type WorkerFailure = {
  ok: false;
  error: string;
};

type WorkerResponse = WorkerSuccess | WorkerFailure;

type WorkerPayload = {
  input: ArrayBuffer;
  inputFormat: InputFormat;
  outputFormat: OutputFormat;
  triangulate: {
    linearDeflection?: number;
    angularDeflection?: number;
    relative?: boolean;
    parallel?: boolean;
  };
  includeBom: boolean;
  includeNodeMap: boolean;
};

function resolveInputFormat(fileName: string): InputFormat | null {
  const ext = fileName.split('.').pop()?.toLowerCase();
  if (!ext) return null;
  if (ext === 'step' || ext === 'stp') return 'step';
  if (ext === 'iges' || ext === 'igs') return 'iges';
  return null;
}

function resolveDownloadName(sourceName: string, format: OutputFormat) {
  const baseName = sourceName.replace(/\.[^/.]+$/, '');
  return `${baseName}.${format}`;
}

function toBase64(data: Uint8Array) {
  let binary = '';
  const chunkSize = 0x8000;
  for (let i = 0; i < data.length; i += chunkSize) {
    const chunk = data.subarray(i, i + chunkSize);
    binary += String.fromCharCode(...chunk);
  }
  return btoa(binary);
}

function createDownloadFromWorkerResult(result: WorkerSuccess, sourceName: string) {
  if (result.outputFormat === 'glb') {
    const blob = new Blob([result.data], { type: 'model/gltf-binary' });
    return {
      url: URL.createObjectURL(blob),
      name: resolveDownloadName(sourceName, 'glb'),
    };
  }

  if (result.outputFormat === 'obj') {
    const blob = new Blob([result.data], { type: 'text/plain' });
    return {
      url: URL.createObjectURL(blob),
      name: resolveDownloadName(sourceName, 'obj'),
    };
  }

  const gltfText = new TextDecoder().decode(result.gltf);
  const gltf = JSON.parse(gltfText) as {
    buffers?: Array<{ uri?: string; byteLength?: number }>;
  };
  if (Array.isArray(gltf.buffers)) {
    const encoded = `data:application/octet-stream;base64,${toBase64(
      new Uint8Array(result.bin)
    )}`;
    gltf.buffers = gltf.buffers.map((buffer) => ({
      ...buffer,
      uri: encoded,
    }));
  }
  const blob = new Blob([JSON.stringify(gltf)], {
    type: 'model/gltf+json',
  });
  return confirmDownload(sourceName, blob, 'gltf');
}

function confirmDownload(sourceName: string, blob: Blob, format: OutputFormat) {
  return {
    url: URL.createObjectURL(blob),
    name: resolveDownloadName(sourceName, format),
  };
}

export function useStepConverterBrowser(t: TranslateFn): StepConverterController {
  const workerRef = useRef<Worker | null>(null);
  const workerRequestIdRef = useRef(0);
  const requestIdRef = useRef(0);

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

  const runWorkerConversion = (payload: WorkerPayload) => {
    const worker = ensureWorker();
    const id = workerRequestIdRef.current + 1;
    workerRequestIdRef.current = id;
    return new Promise<WorkerSuccess>((resolve, reject) => {
      const handleMessage = (event: MessageEvent<WorkerResponse & { id: number }>) => {
        if (event.data.id !== id) return;
        cleanup();
        if (!event.data.ok) {
          reject(new Error(event.data.error));
          return;
        }
        resolve(event.data);
      };
      const handleError = (event: ErrorEvent) => {
        cleanup();
        reject(event.error instanceof Error ? event.error : new Error(event.message));
      };
      const cleanup = () => {
        worker.removeEventListener('message', handleMessage);
        worker.removeEventListener('error', handleError);
      };
      worker.addEventListener('message', handleMessage);
      worker.addEventListener('error', handleError);
      worker.postMessage({ id, ...payload }, [payload.input]);
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

  const onReset = () => {
    requestIdRef.current += 1;
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
    setMetadataStatus({
      state:
        isAdvanced && (includeBom || includeNodeMap) ? 'loading' : 'idle',
    });
    clearDownloads();

    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;

    try {
      const inputFormat = resolveInputFormat(file.name);
      if (!inputFormat) {
        setStatus({
          state: 'error',
          message: t('tools.stepConverter.status.error'),
        });
        return;
      }

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
        input: inputBuffer,
        inputFormat,
        outputFormat: format,
        triangulate: triangulateOptions,
        includeBom: isAdvanced && includeBom,
        includeNodeMap: isAdvanced && includeNodeMap,
      });
      if (requestIdRef.current !== requestId) return;

      const output = createDownloadFromWorkerResult(result, file.name);
      setDownload(output);
      setStatus({ state: 'success' });

      if (isAdvanced && (includeBom || includeNodeMap)) {
        if (result.bom && includeBom) {
          setBom(
            createJsonDownload(result.bom, buildMetadataName(file.name, 'bom'))
          );
        }
        if (result.nodeMap && includeNodeMap) {
          setNodeMap(
            createJsonDownload(
              result.nodeMap,
              buildMetadataName(file.name, 'node-map')
            )
          );
        }
        setMetadataStatus({ state: 'success' });
      }
    } catch (error) {
      if (requestIdRef.current !== requestId) return;
      setStatus({
        state: 'error',
        message:
          error instanceof Error
            ? error.message
            : t('tools.stepConverter.status.error'),
      });
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
    onCancel,
  };
}
