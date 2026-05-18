// OCAF label entries are colon-delimited digit runs (e.g. "0:1:1:16:8").
// They can appear adjacent to underscores or other word characters in GLB node names,
// so word-boundary anchors (\b) are intentionally avoided.
const OCAF_ENTRY_RE = /\d+(?::\d+)+/g;

export function extractOcafEntry(name: string): string | null {
  const matches = name.match(OCAF_ENTRY_RE);
  return matches ? matches[matches.length - 1] : null;
}
