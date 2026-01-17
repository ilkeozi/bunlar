import type { NameFormat, OutputFormat, ReadOptions, TriangulateOptions } from '../core/types';
import { NAME_FORMAT_KEYS } from '../core/name-format';

export type ParsedArgs = {
  input: string | null;
  output: string | null;
  bomOut: string | null;
  nodeMapOut: string | null;
  format: OutputFormat | null;
  nameFormat: NameFormat | null;
  readOptions: ReadOptions;
  triangulateOptions: TriangulateOptions;
  metadata: Record<string, string>;
  help: boolean;
  version: boolean;
  errors: string[];
};

const FORMAT_VALUES: OutputFormat[] = ['obj', 'gltf', 'glb'];

export function parseArgs(argv: string[]): ParsedArgs {
  const readOptions: ReadOptions = {
    preserveNames: true,
    preserveColors: true,
    preserveLayers: true,
    preserveMaterials: true,
  };
  const triangulateOptions: TriangulateOptions = {
    linearDeflection: 0.1,
    angularDeflection: 0.1,
    relative: false,
    parallel: false,
  };

  const metadata: Record<string, string> = {};
  const errors: string[] = [];
  let input: string | null = null;
  let output: string | null = null;
  let bomOut: string | null = null;
  let nodeMapOut: string | null = null;
  let format: OutputFormat | null = null;
  let nameFormat: NameFormat | null = null;
  let help = false;
  let version = false;

  const normalizedNameFormats = buildNameFormatMap();

  function takeValue(arg: string, next: string | undefined) {
    if (arg.includes('=')) {
      return arg.split('=')[1] ?? null;
    }
    return next ?? null;
  }

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--help' || arg === '-h') {
      help = true;
    } else if (arg === '--version' || arg === '-v') {
      version = true;
    } else if (arg === '--input' || arg === '-i') {
      input = takeValue(arg, argv[++i]);
      if (!input) {
        errors.push('Missing value for --input.');
      }
    } else if (arg === '--output' || arg === '-o') {
      output = takeValue(arg, argv[++i]);
      if (!output) {
        errors.push('Missing value for --output.');
      }
    } else if (arg === '--bom-out') {
      bomOut = takeValue(arg, argv[++i]);
      if (!bomOut) {
        errors.push('Missing value for --bom-out.');
      }
    } else if (arg === '--node-map-out') {
      nodeMapOut = takeValue(arg, argv[++i]);
      if (!nodeMapOut) {
        errors.push('Missing value for --node-map-out.');
      }
    } else if (arg === '--format' || arg === '-f') {
      const value = takeValue(arg, argv[++i]);
      if (!value) {
        errors.push('Missing value for --format.');
      } else if (FORMAT_VALUES.includes(value.toLowerCase() as OutputFormat)) {
        format = value.toLowerCase() as OutputFormat;
      } else {
        errors.push(`Unsupported --format value "${value}".`);
      }
    } else if (arg === '--name-format') {
      const value = takeValue(arg, argv[++i]);
      if (!value) {
        errors.push('Missing value for --name-format.');
      } else {
        const normalized = normalizeNameFormat(value);
        const resolved = normalizedNameFormats.get(normalized);
        if (!resolved) {
          errors.push(`Unsupported --name-format value "${value}".`);
        } else {
          nameFormat = resolved;
        }
      }
    } else if (arg === '--linDeflection' || arg === '--lin-deflection') {
      const value = takeValue(arg, argv[++i]);
      if (!value) {
        errors.push('Missing value for --lin-deflection.');
      } else {
        triangulateOptions.linearDeflection = Number(value);
      }
    } else if (arg === '--angDeflection' || arg === '--ang-deflection') {
      const value = takeValue(arg, argv[++i]);
      if (!value) {
        errors.push('Missing value for --ang-deflection.');
      } else {
        triangulateOptions.angularDeflection = Number(value);
      }
    } else if (arg === '--relative') {
      triangulateOptions.relative = true;
    } else if (arg === '--parallel') {
      triangulateOptions.parallel = true;
    } else if (arg === '--no-names') {
      readOptions.preserveNames = false;
    } else if (arg === '--no-colors') {
      readOptions.preserveColors = false;
    } else if (arg === '--no-layers') {
      readOptions.preserveLayers = false;
    } else if (arg === '--no-materials') {
      readOptions.preserveMaterials = false;
    } else if (arg === '--metadata') {
      const kv = takeValue(arg, argv[++i]);
      if (!kv) {
        errors.push('Missing value for --metadata.');
      } else if (!kv.includes('=')) {
        errors.push('Metadata must be in key=value format.');
      } else {
        const [key, value] = kv.split('=');
        metadata[key] = value;
      }
    } else if (arg.startsWith('-')) {
      errors.push(`Unknown option "${arg}".`);
    } else {
      errors.push(`Unexpected argument "${arg}".`);
    }
  }

  return {
    input,
    output,
    bomOut,
    nodeMapOut,
    format,
    nameFormat,
    readOptions,
    triangulateOptions,
    metadata,
    help,
    version,
    errors,
  };
}

function normalizeNameFormat(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]/g, '');
}

function buildNameFormatMap() {
  const map = new Map<string, NameFormat>();
  (Object.keys(NAME_FORMAT_KEYS) as NameFormat[]).forEach((format) => {
    map.set(normalizeNameFormat(format), format);
  });
  return map;
}
