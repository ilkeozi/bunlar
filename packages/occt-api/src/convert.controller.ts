import { Body, Controller, Get, Post, Res, UploadedFile, UseInterceptors } from "@nestjs/common";
import { FileInterceptor } from "@nestjs/platform-express";
import type { Response } from "express";
import { diskStorage } from "multer";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { ConvertService, ConvertRequest, MetadataRequest } from "./convert.service";

const UPLOAD_DIR = path.join(os.tmpdir(), "occt-api");

@Controller()
export class ConvertController {
  constructor(private readonly convertService: ConvertService) {}

  @Get("/health")
  health() {
    return { ok: true };
  }

  @Post("/convert")
  async convert(@Body() body: ConvertRequest) {
    return this.convertService.convert(body);
  }

  @Post("/convert/upload")
  @UseInterceptors(
    FileInterceptor("file", {
      storage: diskStorage({
        destination: (_req, _file, cb) => {
          fs.mkdirSync(UPLOAD_DIR, { recursive: true });
          cb(null, UPLOAD_DIR);
        },
        filename: (_req, file, cb) => {
          const ext = path.extname(file.originalname);
          cb(null, `${crypto.randomUUID()}${ext}`);
        }
      })
    })
  )
  async convertUpload(
    @UploadedFile() file: Express.Multer.File,
    @Body() body: Record<string, string>,
    @Res() res: Response
  ) {
    if (!file) {
      return res.status(400).json({ ok: false, error: "Missing file upload." });
    }

    const startedAt = Date.now();
    const format = normalizeFormat(body.format) ?? "gltf";
    const baseName = path.parse(file.filename).name;
    const outputPath = path.join(UPLOAD_DIR, `${baseName}.${format}`);

    console.log("[occt-api] convert/upload start", {
      name: file.originalname,
      size: file.size,
      format,
      linDeflection: body.linDeflection,
      angDeflection: body.angDeflection,
      relative: body.relative,
      parallel: body.parallel
    });

    const result = await this.convertService.convert({
      inputPath: file.path,
      outputPath,
      format,
      linDeflection: parseNumber(body.linDeflection),
      angDeflection: parseNumber(body.angDeflection),
      relative: parseBool(body.relative),
      parallel: parseBool(body.parallel)
    });

    console.log("[occt-api] convert/upload done", {
      ok: result.ok,
      ms: Date.now() - startedAt,
      error: result.ok ? undefined : result.error
    });

    if (!result.ok) {
      cleanupFiles([file.path, outputPath, outputPath.replace(/\.gltf$/, ".bin")]);
      return res.status(400).json(result);
    }

    const binPath = outputPath.replace(/\.gltf$/, ".bin");

    res.on("finish", () => {
      cleanupFiles([file.path, outputPath, binPath]);
    });

    if (format === "gltf" && fs.existsSync(binPath)) {
      const gltfText = fs.readFileSync(outputPath, "utf8");
      const gltf = JSON.parse(gltfText) as {
        buffers?: Array<{ uri?: string; byteLength?: number }>;
      };
      const bin = fs.readFileSync(binPath);

      if (Array.isArray(gltf.buffers)) {
        const encoded = `data:application/octet-stream;base64,${bin.toString("base64")}`;
        gltf.buffers = gltf.buffers.map((buffer) => ({
          ...buffer,
          uri: encoded
        }));
      }

      res.setHeader("Content-Type", "model/gltf+json");
      res.setHeader(
        "Content-Disposition",
        `attachment; filename="${path.basename(outputPath)}"`
      );
      return res.send(JSON.stringify(gltf));
    }

    return res.download(outputPath);
  }

  @Post("/convert/metadata/upload")
  @UseInterceptors(
    FileInterceptor("file", {
      storage: diskStorage({
        destination: (_req, _file, cb) => {
          fs.mkdirSync(UPLOAD_DIR, { recursive: true });
          cb(null, UPLOAD_DIR);
        },
        filename: (_req, file, cb) => {
          const ext = path.extname(file.originalname);
          cb(null, `${crypto.randomUUID()}${ext}`);
        }
      })
    })
  )
  async convertMetadataUpload(
    @UploadedFile() file: Express.Multer.File,
    @Body() body: Record<string, string>,
    @Res() res: Response
  ) {
    if (!file) {
      return res.status(400).json({ ok: false, error: "Missing file upload." });
    }

    const includeBom = parseBool(body.includeBom);
    const includeNodeMap = parseBool(body.includeNodeMap);

    const result = await this.convertService.extractMetadata({
      inputPath: file.path,
      includeBom: includeBom || includeNodeMap ? includeBom : true,
      includeNodeMap: includeBom || includeNodeMap ? includeNodeMap : true
    } satisfies MetadataRequest);

    cleanupFiles([file.path]);

    if (!result.ok) {
      return res.status(400).json(result);
    }

    return res.json(result);
  }
}

function normalizeFormat(value: string | undefined) {
  if (!value) return null;
  const lowered = value.toLowerCase();
  if (lowered === "obj" || lowered === "gltf" || lowered === "glb") {
    return lowered;
  }
  return null;
}

function parseNumber(value: string | undefined) {
  if (value === undefined) return undefined;
  const num = Number(value);
  return Number.isNaN(num) ? undefined : num;
}

function parseBool(value: string | undefined) {
  if (value === undefined || value === "") return undefined;
  return value === "true" || value === "1";
}

function cleanupFiles(paths: string[]) {
  for (const filePath of paths) {
    if (!filePath) continue;
    try {
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }
    } catch {
      // best effort cleanup
    }
  }
}
