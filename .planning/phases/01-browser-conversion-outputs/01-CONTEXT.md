# Phase 1: Browser Conversion + Outputs - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver browser-based STEP conversion that reliably produces downloadable GLB plus assembly metadata, with progress/cancel and actionable errors.

</domain>

<decisions>
## Implementation Decisions

### Input handling & limits

- Enforce the 15 MB size cap on file select (block before conversion starts)
- Do basic upfront validation (file type + size); deeper checks during conversion
- Unsupported STEP content should fail fast with an actionable summary error

### Output packaging

- Provide a single download bundle containing GLB + metadata
- Embed metadata inside GLB and also provide JSON sidecar in the bundle
- Use the input filename for output naming
- Do not provide partial outputs on failure

### Metadata structure

- BOM includes name + quantity only
- Use stable string IDs for nodes
- Node map is one-to-one between tree nodes and mesh entries
- Include a top-level schema version field

### Progress + cancellation behavior

- Progress is stage-based (e.g., parsing, meshing, packaging)
- Cancel should immediately stop conversion and produce no outputs
- After cancel, keep the file selected and allow retry
- On errors, provide a retry action

### Claude's Discretion

None specified.

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

_Phase: 01-browser-conversion-outputs_
_Context gathered: 2026-01-31_
