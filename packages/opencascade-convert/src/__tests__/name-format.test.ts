import { describe, expect, it } from 'vitest';
import { DEFAULT_NAME_FORMAT, NAME_FORMAT_KEYS, resolveNameFormatKey } from '../core/name-format';

describe('name format mapping', () => {
  it('uses the default when no format is provided', () => {
    expect(resolveNameFormatKey()).toBe(NAME_FORMAT_KEYS[DEFAULT_NAME_FORMAT]);
  });

  it('maps each supported format to a mesh name key', () => {
    (Object.keys(NAME_FORMAT_KEYS) as Array<keyof typeof NAME_FORMAT_KEYS>).forEach((key) => {
      expect(resolveNameFormatKey(key)).toBe(NAME_FORMAT_KEYS[key]);
    });
  });

  it('falls back to the default for unknown values', () => {
    expect(resolveNameFormatKey('unknown' as never)).toBe(NAME_FORMAT_KEYS[DEFAULT_NAME_FORMAT]);
  });
});
