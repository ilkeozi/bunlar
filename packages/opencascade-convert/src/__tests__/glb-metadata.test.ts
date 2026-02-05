import { describe, expect, it } from 'vitest';

import { injectAssetExtrasIntoGlb } from '../occt/glb-metadata';

const GLB_MAGIC = 0x46546c67; // 'glTF'
const GLB_VERSION_2 = 2;

const CHUNK_TYPE_JSON = 0x4e4f534a; // 'JSON'
const CHUNK_TYPE_BIN = 0x004e4942; // 'BIN\0'

function padTo4(bytes: Uint8Array, padByte: number) {
  const paddedLength = Math.ceil(bytes.byteLength / 4) * 4;
  if (paddedLength === bytes.byteLength) {
    return bytes;
  }
  const out = new Uint8Array(paddedLength);
  out.set(bytes);
  out.fill(padByte, bytes.byteLength);
  return out;
}

function encodeUtf8(text: string) {
  return new TextEncoder().encode(text);
}

function decodeUtf8(bytes: Uint8Array) {
  return new TextDecoder('utf-8').decode(bytes);
}

type GlbChunk = {
  type: number;
  data: Uint8Array;
};

function buildGlb(chunks: Array<{ type: number; data: Uint8Array }>) {
  const headerLength = 12;
  const chunkHeaderLength = 8;

  const chunkBytes = chunks.map(({ type, data }) => {
    const padByte = type === CHUNK_TYPE_JSON ? 0x20 : 0x00;
    const padded = padTo4(data, padByte);
    const chunk = new Uint8Array(chunkHeaderLength + padded.byteLength);
    const view = new DataView(chunk.buffer);
    view.setUint32(0, padded.byteLength, true);
    view.setUint32(4, type, true);
    chunk.set(padded, chunkHeaderLength);
    return chunk;
  });

  const totalLength =
    headerLength + chunkBytes.reduce((sum, b) => sum + b.byteLength, 0);
  const out = new Uint8Array(totalLength);
  const view = new DataView(out.buffer);
  view.setUint32(0, GLB_MAGIC, true);
  view.setUint32(4, GLB_VERSION_2, true);
  view.setUint32(8, totalLength, true);

  let offset = headerLength;
  for (const chunk of chunkBytes) {
    out.set(chunk, offset);
    offset += chunk.byteLength;
  }

  return out;
}

function parseGlb(glb: Uint8Array): {
  version: number;
  length: number;
  chunks: GlbChunk[];
} {
  if (glb.byteLength < 12) {
    throw new Error('GLB too small');
  }
  const view = new DataView(glb.buffer, glb.byteOffset, glb.byteLength);
  const magic = view.getUint32(0, true);
  const version = view.getUint32(4, true);
  const length = view.getUint32(8, true);
  if (magic !== GLB_MAGIC) {
    throw new Error('Not a GLB');
  }
  if (length !== glb.byteLength) {
    throw new Error('GLB length mismatch');
  }

  const chunks: GlbChunk[] = [];
  let offset = 12;
  while (offset + 8 <= glb.byteLength) {
    const chunkLength = view.getUint32(offset, true);
    const chunkType = view.getUint32(offset + 4, true);
    const start = offset + 8;
    const end = start + chunkLength;
    if (end > glb.byteLength) {
      throw new Error('GLB chunk truncated');
    }
    chunks.push({ type: chunkType, data: glb.subarray(start, end) });
    offset = end;
  }

  return { version, length, chunks };
}

function extractJsonChunk(glb: Uint8Array) {
  const parsed = parseGlb(glb);
  const jsonChunk = parsed.chunks.find((c) => c.type === CHUNK_TYPE_JSON);
  if (!jsonChunk) {
    throw new Error('Missing JSON chunk');
  }
  return JSON.parse(decodeUtf8(jsonChunk.data).trim());
}

describe('injectAssetExtrasIntoGlb', () => {
  it('injects into GLB that has asset but no extras', () => {
    const json = {
      asset: { version: '2.0', generator: 'test' },
      nodes: [{ name: 'a' }],
    };
    const binData = new Uint8Array([1, 2, 3, 4]);
    const customChunkData = new Uint8Array([9, 8, 7, 6]);
    const customChunkType = 0x12345678;

    const input = buildGlb([
      { type: CHUNK_TYPE_JSON, data: encodeUtf8(JSON.stringify(json)) },
      { type: CHUNK_TYPE_BIN, data: binData },
      { type: customChunkType, data: customChunkData },
    ]);

    const out = injectAssetExtrasIntoGlb(input, {
      schemaVersion: 1,
      assemblyId: 'asm-1',
    });
    expect(out).toBeInstanceOf(Uint8Array);

    const outParsed = parseGlb(out);
    expect(outParsed.version).toBe(GLB_VERSION_2);
    expect(outParsed.length).toBe(out.byteLength);

    const outJson = extractJsonChunk(out);
    expect(outJson.asset).toBeTruthy();
    expect(outJson.asset.extras).toEqual({
      schemaVersion: 1,
      assemblyId: 'asm-1',
    });

    const inputParsed = parseGlb(input);
    const inputBin = inputParsed.chunks.find(
      (c) => c.type === CHUNK_TYPE_BIN
    )?.data;
    const outBin = outParsed.chunks.find(
      (c) => c.type === CHUNK_TYPE_BIN
    )?.data;
    expect(outBin).toEqual(inputBin);

    const inputCustom = inputParsed.chunks.find(
      (c) => c.type === customChunkType
    )?.data;
    const outCustom = outParsed.chunks.find(
      (c) => c.type === customChunkType
    )?.data;
    expect(outCustom).toEqual(inputCustom);
  });

  it('merges into existing asset.extras without dropping keys', () => {
    const json = {
      asset: { version: '2.0', extras: { keepMe: true, nested: { a: 1 } } },
      scenes: [{ nodes: [0] }],
      nodes: [{}],
    };
    const input = buildGlb([
      { type: CHUNK_TYPE_JSON, data: encodeUtf8(JSON.stringify(json)) },
    ]);

    const out = injectAssetExtrasIntoGlb(input, { addMe: 123 });
    const outJson = extractJsonChunk(out);

    expect(outJson.asset.extras).toEqual({
      keepMe: true,
      nested: { a: 1 },
      addMe: 123,
    });
  });

  it('throws a clear error for invalid GLB data', () => {
    const wrongMagic = new Uint8Array([0, 1, 2, 3, 4, 5, 6, 7]);
    expect(() => injectAssetExtrasIntoGlb(wrongMagic, { a: 1 })).toThrow(
      /invalid glb/i
    );
    expect(() => injectAssetExtrasIntoGlb(wrongMagic, { a: 1 })).toThrow(
      /magic/i
    );

    const truncated = new Uint8Array(12 + 8);
    const view = new DataView(truncated.buffer);
    view.setUint32(0, GLB_MAGIC, true);
    view.setUint32(4, GLB_VERSION_2, true);
    view.setUint32(8, 12 + 8 + 4, true);
    view.setUint32(12, 4, true);
    view.setUint32(16, CHUNK_TYPE_JSON, true);
    expect(() => injectAssetExtrasIntoGlb(truncated, { a: 1 })).toThrow(
      /invalid glb/i
    );
    expect(() => injectAssetExtrasIntoGlb(truncated, { a: 1 })).toThrow(
      /truncat|missing/i
    );
  });
});
