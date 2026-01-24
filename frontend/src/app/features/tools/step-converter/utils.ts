import type { OutputFormat } from './types';

export function resolveApiBase() {
  const raw = import.meta.env.VITE_OCCT_API_URL as string | undefined;
  const base = raw && raw.trim().length > 0 ? raw : 'http://localhost:3001';
  return base.replace(/\/$/, '');
}

export function resolveDownloadName(
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

export async function fetchMetadata(
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
    return {
      ok: false,
      error: error instanceof Error ? error.message : 'Request failed.',
    };
  }
}

export function createJsonDownload(payload: unknown, name: string) {
  const json = JSON.stringify(payload, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  return { url, name };
}

export function buildMetadataName(
  sourceName: string,
  suffix: 'bom' | 'node-map'
) {
  const baseName = sourceName.replace(/\.[^/.]+$/, '');
  return `${baseName}.${suffix}.json`;
}
