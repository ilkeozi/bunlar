const OCAF_ENTRY_RE = /\b\d+(?::\d+)+\b/g;

export function extractOcafEntry(name: string): string | null {
  const matches = name.match(OCAF_ENTRY_RE);
  return matches ? matches[matches.length - 1] : null;
}
