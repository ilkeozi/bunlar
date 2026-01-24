import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import type { LoaderOptions } from '../core/types';
import type { OpenCascadeInstance } from './types';

export type { OpenCascadeInstance } from './types';

let cachedPromise: Promise<OpenCascadeInstance> | null = null;

export async function loadOpenCascade({ cwd }: LoaderOptions = {}): Promise<OpenCascadeInstance> {
  const specifier = 'opencascade.js/dist/node.js';
  if (cwd) {
    try {
      const require = createRequire(__filename);
      const entryPath = require.resolve(specifier, {
        paths: [cwd],
      });
      const module = await import(pathToFileURL(entryPath).href);
      const initOpenCascade = resolveInitOpenCascade(module, entryPath);
      return initOpenCascade();
    } catch (error) {
      if (!isModuleNotFound(error)) {
        throw error;
      }
    }
  }
  const module = await import(specifier);
  const initOpenCascade = resolveInitOpenCascade(module, specifier);
  return initOpenCascade();
}

export async function getOpenCascade(options: LoaderOptions = {}): Promise<OpenCascadeInstance> {
  const shouldCache = options.cache !== false;
  if (!shouldCache) {
    return loadOpenCascade(options);
  }
  if (!cachedPromise) {
    cachedPromise = loadOpenCascade(options);
  }
  return cachedPromise;
}

function resolveInitOpenCascade(
  module: unknown,
  sourcePath: string
): () => Promise<OpenCascadeInstance> {
  if (typeof module === 'function') {
    return module as () => Promise<OpenCascadeInstance>;
  }
  if (module && typeof module === 'object') {
    const typed = module as { default?: unknown; initOpenCascade?: unknown };
    if (typeof typed.default === 'function') {
      return typed.default as () => Promise<OpenCascadeInstance>;
    }
    if (typeof typed.initOpenCascade === 'function') {
      return typed.initOpenCascade as () => Promise<OpenCascadeInstance>;
    }
  }
  throw new Error(`opencascade.js entry ${sourcePath} did not export an init function.`);
}

function isModuleNotFound(error: unknown) {
  if (!error || typeof error !== 'object') {
    return false;
  }
  const code = (error as { code?: string }).code;
  return code === 'ERR_MODULE_NOT_FOUND' || code === 'MODULE_NOT_FOUND';
}
