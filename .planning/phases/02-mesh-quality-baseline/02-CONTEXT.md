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

- Avoid both FPS drops and input lag; neither is acceptable.

### Claude's Discretion

- How to measure/track FPS and interaction latency (instrumentation approach).
- Which representative test models to use to approximate the 200-part workload.
- Exact knobs and heuristics to tune mesh output, as long as targets above are met.

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
