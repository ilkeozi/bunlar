# Phase 03: Explorer Selection Workflow - Research

**Researched:** 2026-02-07
**Domain:** React + React Three Fiber selection syncing, assembly tree, visibility/isolation, camera fit
**Confidence:** HIGH

## Summary

Phase 03 should be implemented as a single source of truth selection/visibility store that both the Assembly Explorer tree and the 3D canvas read/write. Tree-to-3D sync is a pure mapping problem (tree node id -> part key -> meshes) and 3D-to-tree sync is the inverse (picked mesh -> part key -> tree node id), with the locked semantics enforced at the store boundary (single-select, clear on empty, hidden not pickable, 3D picks frontmost).

The codebase already demonstrates the required highlight style and the preferred R3F pointer model: the carbon-aware motor/gearbox feature adds an edge-outline (`THREE.EdgesGeometry` + `THREE.LineSegments`) to the selected mesh and clears selection via `Canvas onPointerMissed`. Reuse that exact outline construction, generalized to “selected part = N meshes”, and keep it non-pickable (`raycast = () => {}`) like the existing pattern.

Visibility should be modeled as an explicit-hidden set over the assembly tree (supports hide/show on non-leaf nodes affecting subtrees) plus an isolate toggle that swaps in a derived hidden set while preserving a snapshot to restore when isolate turns off. Scene application should be done via a precomputed map (partKey -> meshes[]) to avoid traversing the scene on every toggle.

**Primary recommendation:** Implement a feature-local Zustand store (`selectedNodeId`, `explicitHiddenNodeIds`, `isolate`, `expandedNodeIds`) + two immutable lookup maps (`nodeIdByOcafEntry`, `meshesByOcafEntry`) and wire tree + canvas into it.

## Standard Stack

### Core

| Library            | Version (repo) | Purpose                               | Why Standard                                                              |
| ------------------ | -------------: | ------------------------------------- | ------------------------------------------------------------------------- |
| React              |         19.0.0 | UI + stateful composition             | Existing app baseline                                                     |
| Zustand            |         ^5.0.2 | Shared selection/visibility store     | Already used for app state (`frontend/src/app/state/useLearningStore.ts`) |
| three              |       ^0.171.0 | Scene graph, bounds, outline geometry | Existing 3D baseline                                                      |
| @react-three/fiber |         ^9.0.3 | React renderer + pointer events       | Existing 3D baseline                                                      |
| @react-three/drei  |        ^10.7.6 | `useGLTF`, `OrbitControls`, helpers   | Existing 3D baseline                                                      |
| lucide-react       |       ^0.544.0 | Tree visibility icons, chevrons       | Already used in UI                                                        |

### Supporting

| Library/Tool                | Version (repo) | Purpose                    | When to Use                         |
| --------------------------- | -------------: | -------------------------- | ----------------------------------- |
| Tailwind CSS                |        ^3.4.14 | Tree row styling + dimming | All new UI in `frontend/`           |
| shadcn/ui primitives        |        in repo | Buttons, cards, tooltip    | Toolbar + panels                    |
| Vitest                      |          4.0.9 | Unit tests                 | Pure visibility + mapping functions |
| Playwright                  |        ^1.36.0 | E2E tests                  | Selection sync smoke tests          |
| opencascade-convert/browser |   (transitive) | NodeMap + GLB metadata     | Assembly viewer conversion pipeline |

### Alternatives Considered

| Instead of              | Could Use                               | Tradeoff                                                               |
| ----------------------- | --------------------------------------- | ---------------------------------------------------------------------- |
| Edge-outline highlight  | Postprocessing outline (EffectComposer) | Doesn’t match locked “gearbox highlight style”; adds new dependency    |
| Custom raycasting       | Three `Raycaster` manual                | R3F event intersections already give “frontmost hit”; extra complexity |
| Hand-built tween engine | react-spring                            | Not in repo deps; simple fit animation is small enough to implement    |

## Architecture Patterns

### Recommended Project Structure

Implement Phase 03 inside the existing Assembly Viewer feature to keep conversion, NodeMap, and GLB handling co-located.

```text
frontend/src/app/features/climate-tech/assembly-viewer/
├── components/
│   ├── AssemblyExplorerPanel.tsx        # Tree + toolbar (hide/isolate/fit)
│   ├── AssemblyExplorerTree.tsx         # Expand/collapse + visibility toggles
│   └── AssemblyExplorerToolbar.tsx      # Actions acting on current selection
├── state/
│   └── useAssemblyExplorerStore.ts      # Zustand source of truth
├── utils/
│   ├── ocaf.ts                          # extractOcafEntry(name)
│   ├── nodeMapIndex.ts                  # nodeIdByOcafEntry, descendants, ancestors
│   ├── sceneIndex.ts                    # meshesByOcafEntry, applyVisibility
│   └── fitCamera.ts                     # fit-to-box while keeping OrbitControls target
└── visualizer/
    ├── AssemblyCanvas.tsx               # passes refs + events
    ├── AssemblyModel.tsx                # loads GLB and builds scene index
    └── SelectionOutline.tsx             # attaches outline to selected meshes
```

### Pattern 1: Store-Driven Selection Sync (Single Source of Truth)

**What:** Tree and 3D read/write the same store; mapping is done at the boundary.

**When to use:** Always for EXPL-01/02; avoids divergent “selected mesh” vs “selected node”.

**Implementation notes (locked semantics):**

- Tree can only select leaf part nodes.
- 3D selection picks the frontmost hit.
- Click empty in 3D clears selection.
- 3D-driven selection expands + scrolls to the node.
- Hidden parts remain selectable in tree but stay hidden; hidden parts are not pickable in 3D.

**Example (store shape):**

```ts
// Source: repo pattern uses Zustand create() - frontend/src/app/state/useLearningStore.ts
type SelectSource = 'tree' | '3d' | 'program';

type ExplorerState = {
  selectedNodeId: string | null;
  selectionSource: SelectSource;
  explicitHiddenNodeIds: Set<string>;
  isolateActive: boolean;
  isolateSnapshot: Set<string> | null;
  expandedNodeIds: Set<string>;
  selectNode: (nodeId: string | null, source: SelectSource) => void;
  toggleHidden: (nodeId: string) => void;
  isolateSelection: () => void;
  showAll: () => void;
};
```

### Pattern 2: Highlight = Gearbox Edge-Outline, Generalized

**What:** Attach a non-pickable `LineSegments` outline as a child of each selected mesh.

**When to use:** Always for selected highlight; locked to match carbon-aware motor/gearbox.

**Example:**

```ts
// Source: frontend/src/app/features/climate-tech/carbon-aware-motor-assembly/visualizer/GearboxModel.tsx
const edges = new THREE.EdgesGeometry(selectedMesh.geometry, 35);
const material = new THREE.LineBasicMaterial({
  color: '#7dd3fc',
  transparent: true,
  opacity: 1,
});
material.depthTest = false;
material.depthWrite = false;

const outline = new THREE.LineSegments(edges, material);
outline.name = 'selected-part-outline';
outline.raycast = () => {}; // ensures outline is not pickable
outline.scale.setScalar(1.03);
selectedMesh.add(outline);
```

### Pattern 3: Visibility = Explicit Hidden + Derived Effective Hidden

**What:** Keep user intent as `explicitHiddenNodeIds` and compute effective hidden parts by walking ancestors (assembly hide affects subtree). Apply to scene via partKey->meshes index.

**When to use:** Always; supports hide/show on non-leaf nodes without rewriting the scene graph.

**Recommended model:**

- `explicitHiddenNodeIds`: set of node ids the user explicitly hid.
- `isHiddenEffective(nodeId)`: true if `nodeId` or any ancestor is explicitly hidden, OR isolate mode hides it.
- `hiddenPartEntries`: derived set of leaf part labelEntries that should be invisible in 3D.

### Anti-Patterns to Avoid

- **Dual selection state:** don’t keep both `selectedMesh` and `selectedNodeId` as “authoritative”. Use `selectedNodeId` as truth and derive meshes.
- **Scene traversal on every toggle:** don’t `scene.traverse` on each hide/show; build an index once per model load.
- **Material swapping for highlight:** will diverge from the established gearbox outline feel.

## Don't Hand-Roll

| Problem                          | Don’t Build                                    | Use Instead                              | Why                                                                                   |
| -------------------------------- | ---------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------- |
| Tree + 3D sync state             | prop drilling + local `useState` in both views | Zustand feature store                    | Prevents drift; simplifies E2E assertions                                             |
| 3D picking order                 | custom `Raycaster` sorting                     | R3F pointer events (frontmost hit)       | R3F already provides nearest intersection in event routing; gearbox uses this pattern |
| Outline highlight                | custom shader / postprocessing pipeline        | `EdgesGeometry` + `LineSegments` outline | Matches existing highlight style exactly                                              |
| Fit bounds math                  | ad-hoc “magic numbers”                         | `THREE.Box3`/`Sphere` + FOV math         | Predictable across aspect ratios                                                      |
| Large tree rendering (if needed) | custom DOM virtualization                      | `@tanstack/react-virtual`                | If assemblies get big, virtualization is not worth hand-building (add later)          |

## Common Pitfalls

### Pitfall 1: NodeMap <-> GLB name mismatch

**What goes wrong:** meshes don’t contain OCAF entries, so 3D pick can’t map to tree node.
**Why it happens:** not all GLBs are produced by the converter with `nameFormat: 'productAndInstanceAndOcaf'`.
**How to avoid:** treat OCAF mapping as a requirement for Assembly Viewer GLBs; warn/disable selection if no entries are found during scene indexing.
**Repo evidence:** Assembly viewer converter writes GLB with `nameFormat: 'productAndInstanceAndOcaf'` (`frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts:201`).

### Pitfall 2: Hidden objects still pickable

**What goes wrong:** user hides a part, but can still click-select it in 3D.
**Why it happens:** only UI state changes; scene objects remain visible/raycastable.
**How to avoid:** apply effective hidden state to meshes (`mesh.visible = false`) and ensure any non-geometry helpers have `raycast={() => {}}` like the existing tooltip anchor pattern.
**Repo evidence:** non-pickable objects are implemented by overriding `raycast` (`frontend/src/app/features/climate-tech/carbon-aware-motor-assembly/visualizer/GearboxModel.tsx:286`).

### Pitfall 3: Isolation toggle “forgets” original hidden state

**What goes wrong:** toggling isolate off doesn’t restore the exact previous hide/show configuration.
**Why it happens:** isolate mutates the same set without snapshotting.
**How to avoid:** store a snapshot (copy of `explicitHiddenNodeIds`) at isolate-on time; restore it verbatim at isolate-off time.

### Pitfall 4: Tree auto-reveal fights user expansion

**What goes wrong:** selecting in 3D repeatedly forces expansion changes unexpectedly.
**Why it happens:** effect always expands ancestors, even for tree-driven selection.
**How to avoid:** only auto-expand + scroll when `selectionSource === '3d'`.

### Pitfall 5: Fit animation “retargets” orbit target

**What goes wrong:** camera fits selection but changes orbit pivot.
**Why it happens:** using helpers that set controls target to the bounds center.
**How to avoid:** keep `controls.target` unchanged; move camera position along its current direction from target.

## Code Examples

### 1) Clear selection when clicking empty space

```tsx
// Source: frontend/src/app/features/climate-tech/carbon-aware-motor-assembly/visualizer/GearboxCanvas.tsx
<Canvas onPointerMissed={() => setSelectedPart(null)}>{/* ... */}</Canvas>
```

### 2) Extract OCAF entry from a GLB node name

```ts
// Source: regex pattern in step-converter worker - frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts:424
export function extractOcafEntry(name: string) {
  const matches = name.match(/\b\d+(?::\d+)+\b/g);
  return matches ? matches[matches.length - 1] : null;
}
```

### 3) Build an index for fast scene updates

```ts
// Recommended: build once after GLB clone; use for selection + visibility updates
type MeshIndex = Map<string /* labelEntry */, THREE.Mesh[]>;

function indexMeshesByOcafEntry(model: THREE.Object3D): MeshIndex {
  const map: MeshIndex = new Map();
  model.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (mesh?.isMesh !== true) return;
    const entry = extractOcafEntry(mesh.name ?? '');
    if (!entry) return;
    const list = map.get(entry) ?? [];
    list.push(mesh);
    map.set(entry, list);
  });
  return map;
}
```

### 4) Fit-to-bounds while keeping OrbitControls target

```ts
// Recommended: compute desired camera distance and animate camera.position only
function computeFitPosition(params: {
  camera: THREE.PerspectiveCamera;
  target: THREE.Vector3;
  bounds: THREE.Box3;
  margin?: number;
}) {
  const { camera, target, bounds, margin = 1.15 } = params;
  const sphere = bounds.getBoundingSphere(new THREE.Sphere());
  const radius = sphere.radius * margin;
  if (!Number.isFinite(radius) || radius <= 0) return null;

  const vFov = THREE.MathUtils.degToRad(camera.fov);
  const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
  const fov = Math.min(vFov, hFov);
  const distance = radius / Math.sin(fov / 2);

  const dir = camera.position.clone().sub(target).normalize();
  return target.clone().addScaledVector(dir, distance);
}
```

## State of the Art

| Old Approach                   | Current Approach (recommended)                 | When Changed    | Impact                                                 |
| ------------------------------ | ---------------------------------------------- | --------------- | ------------------------------------------------------ |
| Local component state per view | Feature-local Zustand store as source of truth | N/A             | Enables reliable tree<->3D sync and E2E assertions     |
| Postprocessing outlines        | Edge-outline attachment per selected mesh      | Already in repo | Matches the locked highlight style and avoids new deps |

## Open Questions

1. **Isolation behavior when selection is hidden**

   - What we know: hidden-selected must remain selected; isolate toggles restore prior visibility when turned off.
   - What’s unclear: whether isolate should temporarily force-show the selected part even if it was hidden.
   - Recommendation: default to “isolate shows selection regardless of prior hidden” (but restore snapshot on isolate off). If this feels wrong in UX review, change isolate-on behavior only; the store model remains the same.

2. **Playwright fixture for deterministic selection tests**
   - What we know: current `frontend-e2e/` fixtures only include `empty.step`.
   - What’s unclear: which small STEP/GLB+NodeMap fixture will be used to test selection and visibility reliably.
   - Recommendation: add a tiny STEP fixture with 3-6 parts (or a prebuilt GLB+NodeMap pair produced by the converter) so E2E can validate EXPL-01..03 without running a large conversion.

## Sources

### Primary (HIGH confidence)

- `frontend/src/app/features/climate-tech/carbon-aware-motor-assembly/visualizer/GearboxModel.tsx` - selected outline construction + non-pickable outline
- `frontend/src/app/features/climate-tech/carbon-aware-motor-assembly/visualizer/GearboxCanvas.tsx` - `onPointerMissed` clears selection
- `frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts` - converter writes GLB with `nameFormat: 'productAndInstanceAndOcaf'`
- `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts` - OCAF entry extraction regex
- `package.json` - versions for React/R3F/drei/three/Zustand/Vitest/Playwright

### Secondary (MEDIUM confidence)

- `frontend/public/models/input.node-map.json` - example NodeMap shape (`id`, `labelEntry`, `parentId`, `children`, `kind`)

### Tertiary (LOW confidence)

- pmndrs docs could not be fetched due to size limits (webfetch 5MB cap): https://docs.pmnd.rs/react-three-fiber/api/events

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - confirmed by repo `package.json`
- Architecture: HIGH - grounded in existing feature layout + existing selection/highlight patterns
- Pitfalls: MEDIUM/HIGH - most come directly from locked requirements + observed code patterns

**Research date:** 2026-02-07
**Valid until:** 2026-03-09 (30 days)
