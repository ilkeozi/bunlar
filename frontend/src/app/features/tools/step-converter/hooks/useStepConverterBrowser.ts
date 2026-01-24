import { useEffect, useRef, useState, type FormEvent } from 'react';
import type {
  ConvertBufferResult,
  InputFormat,
  OpenCascadeConverter,
} from 'opencascade-convert/browser';
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

function createDownloadFromResult(
  result: ConvertBufferResult,
  sourceName: string,
  format: OutputFormat
) {
  if (result.outputFormat === 'glb') {
    const blob = new Blob([result.glb], { type: 'model/gltf-binary' });
    return {
      url: URL.createObjectURL(blob),
      name: resolveDownloadName(sourceName, 'glb'),
    };
  }

  if (result.outputFormat === 'obj') {
    const blob = new Blob([result.obj], { type: 'text/plain' });
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
    const encoded = `data:application/octet-stream;base64,${toBase64(result.bin)}`;
    gltf.buffers = gltf.buffers.map((buffer) => ({
      ...buffer,
      uri: encoded,
    }));
  }
  const blob = new Blob([JSON.stringify(gltf)], {
    type: 'model/gltf+json',
  });
  return {
    url: URL.createObjectURL(blob),
    name: resolveDownloadName(sourceName, 'gltf'),
  };
}

export function useStepConverterBrowser(t: TranslateFn): StepConverterController {
  const converterRef = useRef<Promise<OpenCascadeConverter> | null>(null);
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

  useEffect(() => {
    return () => {
      revokeDownload(download);
      revokeDownload(bom);
      revokeDownload(nodeMap);
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
  };

  const getConverter = () => {
    if (!converterRef.current) {
      converterRef.current = import('opencascade-convert/browser').then(
        ({ createConverter }) => createConverter()
      );
    }
    return converterRef.current;
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

    try {
      const inputFormat = resolveInputFormat(file.name);
      if (!inputFormat) {
        setStatus({
          state: 'error',
          message: t('tools.stepConverter.status.error'),
        });
        return;
      }
      const converter = await getConverter();
      if (requestIdRef.current !== requestId) return;

      const inputBuffer = new Uint8Array(await file.arrayBuffer());
      if (requestIdRef.current !== requestId) return;

      const docHandle = converter.readBuffer(inputBuffer, inputFormat, {
        preserveNames: true,
        preserveColors: true,
        preserveLayers: true,
        preserveMaterials: true,
      });

      const triangulateOptions = isAdvanced
        ? {
            linearDeflection: linNumber,
            angularDeflection: angNumber,
            relative,
            parallel,
          }
        : BASIC_TRIANGULATION;

      converter.triangulate(docHandle.get(), triangulateOptions);

      const result = converter.writeBuffer(docHandle, format, {
        nameFormat: 'productOrInstance',
      });
      if (requestIdRef.current !== requestId) return;

      const output = createDownloadFromResult(result, file.name, format);
      setDownload(output);
      setStatus({ state: 'success' });

      if (isAdvanced && (includeBom || includeNodeMap)) {
        setMetadataStatus({ state: 'loading' });
        try {
          const metadata = converter.createMetadataFromGlb(docHandle);
          if (requestIdRef.current !== requestId) return;
          if (includeBom) {
            setBom(
              createJsonDownload(
                metadata.bom,
                buildMetadataName(file.name, 'bom')
              )
            );
          }
          if (includeNodeMap) {
            setNodeMap(
              createJsonDownload(
                metadata.nodeMap,
                buildMetadataName(file.name, 'node-map')
              )
            );
          }
          setMetadataStatus({ state: 'success' });
        } catch (metadataError) {
          if (requestIdRef.current !== requestId) return;
          setMetadataStatus({
            state: 'error',
            message:
              metadataError instanceof Error
                ? metadataError.message
                : t('tools.stepConverter.status.metadataError'),
          });
        }
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
  };
}
