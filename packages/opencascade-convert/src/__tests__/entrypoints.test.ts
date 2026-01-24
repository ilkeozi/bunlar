import { describe, expect, it } from 'vitest';
import * as nodeEntry from '../index';
import * as browserEntry from '../browser';

describe('entry points', () => {
  it('exposes node entry exports', () => {
    expect(typeof nodeEntry.createConverter).toBe('function');
    expect(typeof nodeEntry.convertFile).toBe('function');
    expect(typeof nodeEntry.convertBuffer).toBe('function');
    expect(typeof nodeEntry.getOpenCascade).toBe('function');
  });

  it('exposes browser entry exports', () => {
    expect(typeof browserEntry.createConverter).toBe('function');
    expect(typeof browserEntry.convertBuffer).toBe('function');
    expect(typeof browserEntry.getOpenCascade).toBe('function');
  });

  it('browser entry does not allow file conversion', async () => {
    await expect(browserEntry.convertFile()).rejects.toThrow(
      'convertFile is only supported in Node.js. Use convertBuffer in the browser.'
    );
  });
});
