import { useCallback, useEffect, useRef, useState } from 'react';
import type { InputFormat } from 'opencascade-convert/browser';
import type { AssemblyMetadata, AssemblyBom, AssemblyNodeMap, TranslateFn } from '../types';
import { isBomLinkedToNodeMap } from '../types';

const BASIC_TRIANGULATION = {
  linearDeflection: 8,
  angularDeflection: 1.5,
  relative: true,
  parallel: true,
};

type WorkerModelSuccess = {
  ok: true;
  phase: 'model';
  data: ArrayBuffer;
};

type WorkerMetadataSuccess = {
  ok: true;
  phase: 'metadata';
  bom: AssemblyBom;
  nodeMap: AssemblyNodeMap;
};

type WorkerFailure = {
  ok: false;
  error: string;
};

type WorkerResponse = (WorkerModelSuccess | WorkerMetadataSuccess | WorkerFailure) & {
  id: number;
};

export type AssemblyFileStatus =
  | 'idle'
  | 'converting'
  | 'loading'
  | 'ready'
  | 'error';

function resolveInputFormat(fileName: string): InputFormat | null {
  const ext = fileName.split('.').pop()?.toLowerCase();
  if (!ext) return null;
  if (ext === 'step' || ext === 'stp') return 'step';
  if (ext === 'iges' || ext === 'igs') return 'iges';
  return null;
}

export function useAssemblyFile(
  t: TranslateFn,
  defaultUrl: string,
  defaultName: string
) {
  const [modelUrl, setModelUrl] = useState(defaultUrl);
  const [fileName, setFileName] = useState(defaultName);
  const [status, setStatus] = useState<AssemblyFileStatus>(
    defaultUrl ? 'loading' : 'idle'
  );
  const [error, setError] = useState<string | null>(null);
  const [isSample, setIsSample] = useState(true);
  const [metadata, setMetadata] = useState<AssemblyMetadata | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const workerRef = useRef<Worker | null>(null);
  const requestIdRef = useRef(0);
  const workerRequestIdRef = useRef(0);

  const revokeObjectUrl = useCallback(() => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  }, []);

  const terminateWorker = useCallback(() => {
    if (workerRef.current) {
      workerRef.current.terminate();
      workerRef.current = null;
    }
  }, []);

  const ensureWorker = useCallback(() => {
    if (!workerRef.current) {
      workerRef.current = new Worker(
        new URL('../workers/assemblyConverter.worker.ts', import.meta.url),
        { type: 'module' }
      );
    }
    return workerRef.current;
  }, []);

  const runWorkerConversion = useCallback(
    (
      payload: { input: ArrayBuffer; inputFormat: InputFormat },
      onModel: (data: ArrayBuffer) => void
    ) => {
      const worker = ensureWorker();
      const id = workerRequestIdRef.current + 1;
      workerRequestIdRef.current = id;

      return new Promise<{ bom: AssemblyBom; nodeMap: AssemblyNodeMap }>(
        (resolve, reject) => {
          let hasModel = false;
          let metadata: { bom: AssemblyBom; nodeMap: AssemblyNodeMap } | null = null;

          const handleMessage = (event: MessageEvent<WorkerResponse>) => {
            if (event.data.id !== id) return;
            if (!event.data.ok) {
              cleanup();
              reject(new Error(event.data.error));
              return;
            }
            if (event.data.phase === 'model') {
              hasModel = true;
              onModel(event.data.data);
              if (metadata) {
                cleanup();
                resolve(metadata);
              }
              return;
            }
            if (event.data.phase === 'metadata') {
              metadata = { bom: event.data.bom, nodeMap: event.data.nodeMap };
              if (hasModel) {
                cleanup();
                resolve(metadata);
              }
            }
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
          worker.postMessage(
            {
              id,
              input: payload.input,
              inputFormat: payload.inputFormat,
              triangulate: BASIC_TRIANGULATION,
            },
            [payload.input]
          );
        }
      );
    },
    [ensureWorker]
  );

  const setModelFromBlob = useCallback(
    (blob: Blob) => {
      revokeObjectUrl();
      const url = URL.createObjectURL(blob);
      objectUrlRef.current = url;
      setModelUrl(url);
    },
    [revokeObjectUrl]
  );


  const resetToSample = useCallback(() => {
    requestIdRef.current += 1;
    revokeObjectUrl();
    setModelUrl(defaultUrl);
    setFileName(defaultName);
    setStatus(defaultUrl ? 'loading' : 'idle');
    setError(null);
    setMetadata(null);
    setIsSample(true);
  }, [defaultName, defaultUrl, revokeObjectUrl]);

  useEffect(() => {
    if (!isSample) {
      return;
    }
    setFileName(defaultName);
    setModelUrl(defaultUrl);
    setStatus(defaultUrl ? 'loading' : 'idle');
  }, [defaultName, defaultUrl, isSample]);

  const setFile = useCallback(
    async (file: File | null) => {
      if (!file) {
        resetToSample();
        return;
      }

      setError(null);
      setMetadata(null);
      const currentRequest = requestIdRef.current + 1;
      requestIdRef.current = currentRequest;
      setIsSample(false);

      const inputFormat = resolveInputFormat(file.name);
      if (!inputFormat) {
        setStatus('error');
        setError(t('assemblyViewer.status.unsupported'));
        return;
      }

      setStatus('converting');
      setFileName(file.name);
      try {
        const result = await runWorkerConversion(
          {
            input: await file.arrayBuffer(),
            inputFormat,
          },
          (data) => {
            if (requestIdRef.current !== currentRequest) {
              return;
            }
            setStatus('loading');
            setModelFromBlob(new Blob([data], { type: 'model/gltf-binary' }));
          }
        );

        if (requestIdRef.current !== currentRequest) {
          return;
        }

        if (!isBomLinkedToNodeMap(result.nodeMap, result.bom)) {
          throw new Error(t('assemblyViewer.status.metadataMismatch'));
        }
        setMetadata({ bom: result.bom, nodeMap: result.nodeMap });
      } catch (conversionError) {
        if (requestIdRef.current !== currentRequest) {
          return;
        }
        setStatus('error');
        setError(
          conversionError instanceof Error
            ? conversionError.message
            : t('assemblyViewer.status.conversionFailed')
        );
      }
    },
    [resetToSample, runWorkerConversion, setModelFromBlob, t]
  );

  const markReady = useCallback(() => {
    setStatus('ready');
  }, []);

  useEffect(() => {
    return () => {
      revokeObjectUrl();
      terminateWorker();
    };
  }, [revokeObjectUrl, terminateWorker]);

  return {
    modelUrl,
    fileName,
    status,
    error,
    isSample,
    metadata,
    setFile,
    resetToSample,
    markReady,
    setStatus,
  };
}
