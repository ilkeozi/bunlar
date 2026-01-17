const GLB_HEADER_LENGTH = 12;
const GLB_CHUNK_HEADER_LENGTH = 8;
const GLB_JSON_CHUNK = 0x4e4f534a;

export type NameOverrideMap = Record<string, string>;

export function extractNameOverridesFromGlb(glb: Buffer): NameOverrideMap {
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

function parseGlbJson(glb: Buffer) {
  if (glb.length < GLB_HEADER_LENGTH + GLB_CHUNK_HEADER_LENGTH) {
    return null;
  }
  if (glb.toString('ascii', 0, 4) !== 'glTF') {
    return null;
  }

  let offset = GLB_HEADER_LENGTH;
  while (offset + GLB_CHUNK_HEADER_LENGTH <= glb.length) {
    const chunkLength = glb.readUInt32LE(offset);
    const chunkType = glb.readUInt32LE(offset + 4);
    const chunkStart = offset + GLB_CHUNK_HEADER_LENGTH;
    const chunkEnd = chunkStart + chunkLength;
    if (chunkEnd > glb.length) {
      return null;
    }

    if (chunkType === GLB_JSON_CHUNK) {
      const jsonText = glb.toString('utf8', chunkStart, chunkEnd);
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
