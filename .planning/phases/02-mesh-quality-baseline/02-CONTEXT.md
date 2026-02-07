# Phase 02: Mesh Quality Baseline - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Improve mesh output quality/performance so converted assemblies remain smooth to interact with in the Explorer (tree + 3D), and avoid "triangle explosions".

In scope: tuning conversion/meshing settings and any lightweight runtime safeguards needed to keep orbit + selection + tree interactions smooth.
Out of scope: new explorer features (selection workflow details are Phase 3).

</domain>

<decisions>
## Implementation Decisions

### Definition of "Smooth" (locked)

- Smoothness includes: orbit/pan/zoom + tree interactions (expand/collapse/scroll) + selection/highlight.
- Smoothness is judged in both places:
  - Explorer page (tree + 3D together)
  - Converter preview (if it exists)

### Performance Baseline (locked)

- Target device: typical Windows laptop with integrated GPU.
- FPS target during normal orbit: 45 fps target, 30 fps minimum.
- Selection/highlight reaction time: up to 250ms is acceptable.
- "Time to first interactive orbit" for a medium model: under 5 seconds.

### Workload Scale (locked)

- Phase 2 baseline workload: up to ~200 parts.

### Interaction Quality (locked)

- Input lag is not acceptable.
- FPS drops are not acceptable in the common case, but if a tradeoff is required to preserve mechanical fidelity, prefer preserving fidelity even if FPS dips below the targets.

### Claude's Discretion

- How to measure/track FPS and interaction latency (instrumentation approach).
- Which representative test models to use to approximate the 200-part workload.
- Exact knobs and heuristics to tune mesh output (triangle counts, mesh settings, runtime simplifications), while honoring the tradeoffs below.

### Quality vs Speed (locked)

- Preserve mechanical fidelity over everything.
- Unacceptable artifacts: holes/cracks, bad normals (wobbly shading), and jagged curves (obvious faceting).
- If targets cannot be met on the baseline device with default settings, prefer keeping quality and allowing FPS to drop (do not silently destroy fidelity).
- Prefer slower conversion if it results in smoother runtime interaction.

### Triangle Explosion Policy (locked)

- Claude chooses the triangle explosion threshold(s) for Phase 2.
- Default behavior when threshold exceeded: auto-adjust to reduce triangles and continue.
- User-facing warning: show only after conversion completes (summary), not mid-conversion.
- Persist warnings in outputs: include machine-readable warnings in metadata (e.g., `metadata.conversionWarnings[]`).

### Mesh Appearance Baseline (locked)

- Default shading: preserve "as-converted" (do not force smooth or faceted globally).
- Sharp edges: mixed policy; preserve only major sharp edges.
- Normals: mixed policy; recompute only if clearly broken.
- Prefer consistent appearance across parts, but allow exceptions for performance.

### Measurement and Pass Criteria (locked)

- Add an on-screen FPS/debug overlay in dev builds.
- Measure both:
  - continuous orbit for ~10s
  - orbit while actively selecting/highlighting parts
- Pass criteria for the ~200-part baseline: meets targets most of the time; occasional dips are acceptable.
- If preview and Explorer disagree, Explorer wins (prioritize tree + 3D together).

</decisions>

<specifics>
## Specific Ideas

No additional style/UX specifics beyond the performance and interaction targets.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

---

_Phase: 02-mesh-quality-baseline_
_Context gathered: 2026-02-07_
