# OCCT API (temporary)

Minimal NestJS wrapper around the `opencascade-convert` library for quick experiments.

## Setup

Install dependencies at the repo root:

```bash
npm install
```

Run the server:

```bash
npx nx run occt-api:serve
```

## Endpoints

### `GET /health`

Returns `{ ok: true }`.

### `POST /convert`

```json
{
  "inputPath": "/abs/path/to/model.step",
  "outputPath": "/abs/path/to/model.gltf",
  "format": "gltf",
  "linDeflection": 0.1,
  "angDeflection": 0.1,
  "relative": false,
  "parallel": false
}
```

This calls the `opencascade-convert` library on the server.

### `POST /convert/upload`

Upload a STEP/IGES file and receive the converted file as a download.

```bash
curl -X POST http://localhost:3001/convert/upload \
  -F file=@/abs/path/to/model.step \
  -F format=gltf
```

Optional fields: `linDeflection`, `angDeflection`, `relative`, `parallel`.
