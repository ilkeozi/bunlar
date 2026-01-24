const GLB_HEADER_LENGTH = 12;
const GLB_CHUNK_HEADER_LENGTH = 8;
const GLB_JSON_CHUNK = 0x4e4f534a;

export type NameOverrideMap = Record<string, string>;

export function extractNameOverridesFromGlb(glb: Uint8Array): NameOverrideMap {
  const json = parseGlbJson(glb);
  if (!json || !Array.isArray(json.nodes)) {
    return {};
  }

  const overrides: NameOverrideMap = {};
  json.nodes.forEach((node: { name?: string }) => {
    if (!node?.name) {
      return;
    }
    const ocaf = extractOcafEntry(node.name);
    if (!ocaf) {
      return;
    }
    if (overrides[ocaf]) {
      return;
    }
    const cleaned = cleanName(node.name);
    if (cleaned) {
      overrides[ocaf] = cleaned;
    }
  });

  return overrides;
}

function parseGlbJson(glb: Uint8Array) {
  if (glb.byteLength < GLB_HEADER_LENGTH + GLB_CHUNK_HEADER_LENGTH) {
    return null;
  }
  if (!isGlbMagic(glb)) {
    return null;
  }

  const view = new DataView(glb.buffer, glb.byteOffset, glb.byteLength);
  let offset = GLB_HEADER_LENGTH;
  while (offset + GLB_CHUNK_HEADER_LENGTH <= glb.byteLength) {
    const chunkLength = view.getUint32(offset, true);
    const chunkType = view.getUint32(offset + 4, true);
    const chunkStart = offset + GLB_CHUNK_HEADER_LENGTH;
    const chunkEnd = chunkStart + chunkLength;
    if (chunkEnd > glb.byteLength) {
      return null;
    }

    if (chunkType === GLB_JSON_CHUNK) {
      const jsonText = decodeUtf8(glb.subarray(chunkStart, chunkEnd));
      try {
        return JSON.parse(jsonText);
      } catch {
        return null;
      }
    }

    offset = chunkEnd;
  }

  return null;
}

function isGlbMagic(glb: Uint8Array) {
  if (glb.byteLength < 4) {
    return false;
  }
  return glb[0] === 0x67 && glb[1] === 0x6c && glb[2] === 0x54 && glb[3] === 0x46;
}

function decodeUtf8(bytes: Uint8Array) {
  if (typeof TextDecoder !== 'undefined') {
    return new TextDecoder('utf-8').decode(bytes);
  }
  if (typeof Buffer !== 'undefined') {
    return Buffer.from(bytes).toString('utf8');
  }
  let result = '';
  for (let index = 0; index < bytes.length; index += 1) {
    result += String.fromCharCode(bytes[index]);
  }
  return result;
}

function extractOcafEntry(name: string) {
  const matches = name.match(/\b\d+(?::\d+)+\b/g);
  return matches ? matches[matches.length - 1] : null;
}

function cleanName(name: string) {
  const parts = name.split(/\s*\[/);
  if (parts.length === 1) {
    return name.trim();
  }

  const cleaned: string[] = [parts[0].trim()];
  for (let index = 1; index < parts.length; index += 1) {
    const segment = parts[index];
    const closeIndex = segment.indexOf(']');
    if (closeIndex === -1) {
      continue;
    }
    const inside = segment.slice(0, closeIndex).trim();
    if (inside === '') {
      continue;
    }
    if (/\b\d+(?::\d+)+\b/.test(inside)) {
      continue;
    }
    if (/NAUO\d+/i.test(inside)) {
      continue;
    }
    cleaned.push(`[${inside}]`);
  }

  const result = cleaned.filter(Boolean).join(' ').replace(/\s+/g, ' ').trim();
  return result || name.trim();
}
