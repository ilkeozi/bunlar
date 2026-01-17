import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { createConverter } from '../../index';

const samplePath = path.resolve(__dirname, '../sample/input.step');

describe('opencascade-convert integration', () => {
  const converterPromise = createConverter();

  it(
    'converts a STEP file to GLB',
    async () => {
      if (!fs.existsSync(samplePath)) {
        throw new Error(`Missing sample file at ${samplePath}`);
      }

      const outputPath = path.join(os.tmpdir(), `occt-sample-${Date.now()}.glb`);
      try {
        const converter = await converterPromise;
        converter.convert({
          inputPath: samplePath,
          outputPath,
          format: 'glb',
          read: {
            preserveNames: true,
            preserveColors: true,
            preserveLayers: true,
            preserveMaterials: true,
          },
        triangulate: {
            linearDeflection: 5.0,
            angularDeflection: 2.0,
            parallel: false,
          },
          write: {
            nameFormat: 'productAndInstanceAndOcaf',
          },
        });

        const stat = fs.statSync(outputPath);
        expect(stat.size).toBeGreaterThan(0);
      } finally {
        if (fs.existsSync(outputPath)) {
          fs.unlinkSync(outputPath);
        }
      }
    },
    300_000
  );
});
