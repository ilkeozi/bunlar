import { describe, expect, it } from 'vitest';

import { extractOcafEntry } from './ocaf';

describe('extractOcafEntry', () => {
  it('returns null when no entry exists', () => {
    expect(extractOcafEntry('nope')).toBe(null);
  });

  it('returns the last match when multiple entries exist', () => {
    expect(extractOcafEntry('0:1:1:1/0:1:1:1:2')).toBe('0:1:1:1:2');
  });

  it('matches entries adjacent to underscores', () => {
    expect(extractOcafEntry('foo_0:1:1:16:8_bar')).toBe('0:1:1:16:8');
  });
});
