#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { createConverter } from './converter';
import { resolveInputFormat, resolveOutputFormat } from './core/formats';
import { NAME_FORMAT_KEYS } from './core/name-format';
import { parseArgs } from './cli/args';

function writeErrorLine(message: string) {
  process.stderr.write(`${message}\n`);
}

function writeLine(message: string) {
  process.stdout.write(`${message}\n`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    return;
  }
  if (args.version) {
    printVersion();
    return;
  }

  if (args.errors.length > 0) {
    args.errors.forEach((error) => writeErrorLine(error));
    writeErrorLine('');
    printUsage();
    process.exit(2);
  }

  if (!args.input || !args.output) {
    writeErrorLine('Both --input and --output are required.');
    printUsage();
    process.exit(2);
  }

  const inputPath = path.resolve(args.input);
  const outputPath = path.resolve(args.output);
  const inputFormat = resolveInputFormat(inputPath);
  if (!inputFormat) {
    writeErrorLine('Input must be STEP or IGES (.step, .stp, .igs, .iges).');
    process.exit(2);
  }
  const format = resolveOutputFormat(outputPath, args.format ?? undefined);
  if (!format) {
    writeErrorLine('Output must be .obj, .gltf, or .glb (or specify --format).');
    process.exit(2);
  }

  const converter = await createConverter();
  const docHandle = converter.read(inputPath, inputFormat, args.readOptions);
  converter.triangulate(docHandle.get(), args.triangulateOptions);
  converter.write(docHandle, outputPath, format, {
    metadata: args.metadata,
    nameFormat: args.nameFormat ?? undefined,
  });

  if (args.nodeMapOut) {
    const nodeMap = converter.createNodeMap(docHandle);
    writeJsonFile(path.resolve(args.nodeMapOut), nodeMap);
  }

  if (args.bomOut) {
    const bom = converter.createBom(docHandle);
    writeJsonFile(path.resolve(args.bomOut), bom);
  }
}

function printUsage() {
  writeLine('Usage: opencascade-convert --input <file.step> --output <file.gltf> [options]');
  writeLine('Try --help for full usage.');
}

function printHelp() {
  const nameFormats = Object.keys(NAME_FORMAT_KEYS).join(', ');
  writeLine('opencascade-convert');
  writeLine('');
  writeLine('Usage:');
  writeLine('  opencascade-convert --input <file.step> --output <file.gltf> [options]');
  writeLine('');
  writeLine('Options:');
  writeLine('  -i, --input <path>            Input STEP/IGES file');
  writeLine('  -o, --output <path>           Output OBJ/GLTF/GLB file');
  writeLine('  -f, --format <obj|gltf|glb>   Output format override');
  writeLine('      --bom-out <path>          Write BOM JSON output');
  writeLine('      --node-map-out <path>     Write assembly node map JSON');
  writeLine(`      --name-format <value>     glTF node/mesh naming (${nameFormats})`);
  writeLine('      --lin-deflection <num>    Linear deflection (mesh quality)');
  writeLine('      --ang-deflection <num>    Angular deflection (mesh quality)');
  writeLine('      --relative                Use relative deflection');
  writeLine('      --parallel                Enable parallel triangulation');
  writeLine('      --metadata key=value      Add metadata entries (repeatable)');
  writeLine('      --no-names                Disable name import');
  writeLine('      --no-colors               Disable color import');
  writeLine('      --no-layers               Disable layer import');
  writeLine('      --no-materials            Disable material import');
  writeLine('  -h, --help                     Show help');
  writeLine('  -v, --version                  Show version');
  writeLine('');
  writeLine('Examples:');
  writeLine('  opencascade-convert --input model.step --output model.glb');
  writeLine('  opencascade-convert --input model.step --output model.gltf --lin-deflection 1');
  writeLine('  opencascade-convert --input model.step --output model.glb --name-format productOrInstance');
  writeLine(
    '  opencascade-convert --input model.step --output model.glb --bom-out bom.json --node-map-out nodes.json'
  );
}

function printVersion() {
  const version = readPackageVersion();
  writeLine(version ?? 'unknown');
}

function readPackageVersion() {
  try {
    const packagePath = path.resolve(__dirname, '..', 'package.json');
    const contents = fs.readFileSync(packagePath, 'utf8');
    const data = JSON.parse(contents) as { version?: string };
    return data.version ?? null;
  } catch {
    return null;
  }
}

function writeJsonFile(targetPath: string, payload: unknown) {
  const dir = path.dirname(targetPath);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(targetPath, `${JSON.stringify(payload, null, 2)}\n`);
}

main().catch((error) => {
  const message = error instanceof Error ? error.stack ?? error.message : String(error);
  process.stderr.write(`${message}\n`);
  process.exit(1);
});
