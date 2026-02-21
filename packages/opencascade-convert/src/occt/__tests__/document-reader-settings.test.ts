import { describe, expect, it } from 'vitest';

import { applyReaderSettings } from '../document';

describe('applyReaderSettings', () => {
  it('enables modes using suffixed OpenCascade.js overloads', () => {
    const calls = {
      name: 0,
      color: 0,
      layer: 0,
      mat: 0,
    };

    const reader = {
      SetNameMode_1(value: boolean) {
        expect(value).toBe(true);
        calls.name += 1;
      },
      SetColorMode_2(value: boolean) {
        expect(value).toBe(true);
        calls.color += 1;
      },
      SetLayerMode(value: boolean) {
        expect(value).toBe(true);
        calls.layer += 1;
      },
      SetMatMode_1(value: boolean) {
        expect(value).toBe(true);
        calls.mat += 1;
      },
    };

    applyReaderSettings(reader, {
      preserveNames: true,
      preserveColors: true,
      preserveLayers: true,
      preserveMaterials: true,
    });

    expect(calls).toEqual({ name: 1, color: 1, layer: 1, mat: 1 });
  });

  it('is a no-op when modes are disabled or setters are missing', () => {
    expect(() =>
      applyReaderSettings(
        {},
        {
          preserveNames: false,
          preserveColors: false,
          preserveLayers: false,
          preserveMaterials: false,
        }
      )
    ).not.toThrow();
  });
});
