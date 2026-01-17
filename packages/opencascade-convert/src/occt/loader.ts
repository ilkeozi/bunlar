import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import type { LoaderOptions } from '../core/types';

export type OpenCascadeInstance = any;

let cachedPromise: Promise<OpenCascadeInstance> | null = null;

export async function loadOpenCascade({ cwd }: LoaderOptions = {}): Promise<OpenCascadeInstance> {
  const require = createRequire(__filename);
  const entryPath = require.resolve('opencascade.js/dist/node.js', {
    paths: [cwd ?? process.cwd()],
  });
  const module = await import(pathToFileURL(entryPath).href);
  const initOpenCascade = module.default ?? module;
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
