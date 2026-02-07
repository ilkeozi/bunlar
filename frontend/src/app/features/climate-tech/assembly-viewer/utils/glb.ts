const OCAF_ENTRY_RE = /\d+(?::\d+)+/g;

function parseGlbJson(glb: Uint8Array): unknown {
  const GLB_HEADER_LENGTH = 12;
  const GLB_CHUNK_HEADER_LENGTH = 8;
  const GLB_JSON_CHUNK = 0x4e4f534a;

  if (glb.byteLength < GLB_HEADER_LENGTH + GLB_CHUNK_HEADER_LENGTH) {
    throw new Error('Invalid GLB: truncated header');
  }

  // magic 'glTF'
  if (
    !(glb[0] === 0x67 && glb[1] === 0x6c && glb[2] === 0x54 && glb[3] === 0x46)
  ) {
    throw new Error('Invalid GLB: invalid magic');
  }

  const view = new DataView(glb.buffer, glb.byteOffset, glb.byteLength);
  let offset = GLB_HEADER_LENGTH;
  while (offset + GLB_CHUNK_HEADER_LENGTH <= glb.byteLength) {
    const chunkLength = view.getUint32(offset, true);
    const chunkType = view.getUint32(offset + 4, true);
    const chunkStart = offset + GLB_CHUNK_HEADER_LENGTH;
    const chunkEnd = chunkStart + chunkLength;
    if (chunkEnd > glb.byteLength) {
      throw new Error('Invalid GLB: truncated chunk');
    }
    if (chunkType === GLB_JSON_CHUNK) {
      const jsonText = new TextDecoder('utf-8').decode(
        glb.subarray(chunkStart, chunkEnd)
      );
      return JSON.parse(jsonText);
    }
    offset = chunkEnd;
  }

  throw new Error('Invalid GLB: missing JSON chunk');
}

type GltfNodeDef = {
  name?: string;
};

type GltfJson = {
  nodes?: GltfNodeDef[];
};

export function buildOcafEntryByGltfNodeIndex(
  glb: Uint8Array
): Map<number, string> {
  const gltf = parseGlbJson(glb) as GltfJson;
  const nodes = Array.isArray(gltf?.nodes) ? gltf.nodes : [];

  const map = new Map<number, string>();
  for (let i = 0; i < nodes.length; i += 1) {
    const name = typeof nodes[i]?.name === 'string' ? nodes[i].name : '';
    if (!name) continue;
    const matches = name.match(OCAF_ENTRY_RE);
    if (!matches || matches.length === 0) continue;
    map.set(i, matches[matches.length - 1]);
  }
  return map;
}
