import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { convertBuffer } from '../../index';

const samplePath = path.resolve(__dirname, '../sample/input.step');

describe('opencascade-convert buffer integration', () => {
  it(
    'converts STEP buffer to GLB buffer',
    async () => {
      if (!fs.existsSync(samplePath)) {
        throw new Error(`Missing sample file at ${samplePath}`);
      }

      const input = fs.readFileSync(samplePath);
      const result = await convertBuffer({
        input,
        inputFormat: 'step',
        outputFormat: 'glb',
        triangulate: {
          linearDeflection: 5.0,
          angularDeflection: 2.0,
          parallel: false,
        },
        write: {
          nameFormat: 'productAndInstanceAndOcaf',
        },
      });

      expect(result.outputFormat).toBe('glb');
      expect(result.glb.byteLength).toBeGreaterThan(0);
    },
    300_000
  );
});
