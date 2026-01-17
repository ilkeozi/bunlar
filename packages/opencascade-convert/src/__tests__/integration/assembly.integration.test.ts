import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { createConverter } from '../../index';

const samplePath = path.resolve(__dirname, '../sample/input.step');

describe('opencascade-convert assembly metadata', () => {
  const converterPromise = createConverter();

  it(
    'builds a node map and BOM from the sample file',
    async () => {
      if (!fs.existsSync(samplePath)) {
        throw new Error(`Missing sample file at ${samplePath}`);
      }

      const converter = await converterPromise;
      const docHandle = converter.read(samplePath, 'step', {
        preserveNames: true,
        preserveColors: true,
        preserveLayers: true,
        preserveMaterials: true,
      });

      const nodeMap = converter.createNodeMap(docHandle);
      const bom = converter.createBom(docHandle);

      expect(nodeMap.roots.length).toBeGreaterThan(0);
      expect(Object.keys(nodeMap.nodes).length).toBeGreaterThan(0);
      nodeMap.roots.forEach((rootId) => {
        expect(nodeMap.nodes[rootId]).toBeDefined();
      });

      expect(bom.roots.length).toBe(nodeMap.roots.length);
      expect(bom.items.length).toBeGreaterThan(0);
      bom.items.forEach((item) => {
        expect(item.productId.length).toBeGreaterThan(0);
        expect(item.quantity).toBeGreaterThan(0);
        expect(item.instances.length).toBeGreaterThan(0);
        item.instances.forEach((instance) => {
          expect(nodeMap.nodes[instance.nodeId]).toBeDefined();
          expect(instance.path.length).toBeGreaterThan(0);
        });
      });
    },
    300_000
  );
});
