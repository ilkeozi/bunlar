import { describe, expect, it } from 'vitest';
import { parseArgs } from '../cli/args';

describe('args helpers', () => {
  it('parseArgs uses defaults', () => {
    const parsed = parseArgs(['--input', 'in.step', '--output', 'out.glb']);
    expect(parsed.input).toBe('in.step');
    expect(parsed.output).toBe('out.glb');
    expect(parsed.errors).toHaveLength(0);
    expect(parsed.readOptions.preserveNames).toBe(true);
    expect(parsed.triangulateOptions.parallel).toBe(false);
    expect(parsed.triangulateOptions.linearDeflection).toBe(0.1);
    expect(parsed.bomOut).toBeNull();
    expect(parsed.nodeMapOut).toBeNull();
  });

  it('parseArgs honors flags', () => {
    const parsed = parseArgs([
      '--input',
      'in.step',
      '--output',
      'out.glb',
      '--no-names',
      '--parallel',
      '--linDeflection',
      '2.5',
      '--metadata',
      'source=unit',
    ]);
    expect(parsed.readOptions.preserveNames).toBe(false);
    expect(parsed.errors).toHaveLength(0);
    expect(parsed.triangulateOptions.parallel).toBe(true);
    expect(parsed.triangulateOptions.linearDeflection).toBe(2.5);
    expect(parsed.metadata.source).toBe('unit');
  });

  it('parses bom and node map outputs', () => {
    const parsed = parseArgs([
      '--input',
      'in.step',
      '--output',
      'out.glb',
      '--bom-out',
      'bom.json',
      '--node-map-out',
      'nodes.json',
    ]);
    expect(parsed.errors).toHaveLength(0);
    expect(parsed.bomOut).toBe('bom.json');
    expect(parsed.nodeMapOut).toBe('nodes.json');
  });

  it('parses name format and flags invalid formats', () => {
    const parsed = parseArgs([
      '--input',
      'in.step',
      '--output',
      'out.glb',
      '--name-format',
      'productOrInstance',
    ]);
    expect(parsed.nameFormat).toBe('productOrInstance');
    expect(parsed.errors).toHaveLength(0);

    const invalid = parseArgs(['--name-format', 'nope']);
    expect(invalid.errors.length).toBeGreaterThan(0);
  });
});
