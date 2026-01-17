import path from 'node:path';
import type { InputFormat, OutputFormat } from './types';

const INPUT_EXTENSIONS: Record<InputFormat, string[]> = {
  step: ['.step', '.stp'],
  iges: ['.iges', '.igs'],
};

const OUTPUT_EXTENSIONS: Record<OutputFormat, string[]> = {
  obj: ['.obj'],
  gltf: ['.gltf'],
  glb: ['.glb'],
};

export function resolveInputFormat(inputPath: string): InputFormat | null {
  const ext = path.extname(inputPath).toLowerCase();
  for (const [format, extensions] of Object.entries(INPUT_EXTENSIONS)) {
    if (extensions.includes(ext)) {
      return format as InputFormat;
    }
  }
  return null;
}

export function resolveOutputFormat(outputPath: string, format?: OutputFormat): OutputFormat | null {
  if (format) {
    return format;
  }
  const ext = path.extname(outputPath).toLowerCase();
  for (const [candidate, extensions] of Object.entries(OUTPUT_EXTENSIONS)) {
    if (extensions.includes(ext)) {
      return candidate as OutputFormat;
    }
  }
  return null;
}
