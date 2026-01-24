/// <reference types='vitest' />
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const workspaceRoot = fileURLToPath(new URL('..', import.meta.url));
const ocBrowserEntry = fileURLToPath(
  new URL('../packages/opencascade-convert/src/browser/index.ts', import.meta.url)
);

export default defineConfig({
  root: __dirname,
  cacheDir: '../node_modules/.vite/frontend',
  server: {
    port: 4200,
    host: 'localhost',
    fs: {
      allow: [workspaceRoot],
    },
  },
  preview: {
    port: 4200,
    host: 'localhost',
  },
  plugins: [react()],
  assetsInclude: ['**/*.glb', '**/*.wasm'],
  worker: {
    format: 'es',
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      'opencascade-convert/browser': ocBrowserEntry,
    },
  },
  // Uncomment this if you are using workers.
  // worker: {
  //  plugins: [ nxViteTsPaths() ],
  // },
  build: {
    outDir: './dist',
    emptyOutDir: true,
    reportCompressedSize: true,
    commonjsOptions: {
      transformMixedEsModules: true,
    },
  },
});
