# Phase 3: Explorer Selection Workflow - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement an Assembly Explorer selection workflow where the tree and 3D view stay synchronized:

- Select in tree -> highlight corresponding geometry in 3D
- Select in 3D -> highlight corresponding tree node
- Manage visibility (hide/isolate) and fit camera to current selection / visible set

Out of scope for this phase: new conversion features, new metadata formats, or advanced search/filter tools.

</domain>

<decisions>
## Implementation Decisions

### Selection model (tree + 3D)

- Default selection mode: single-select only.
- Tree selection: only leaf/part nodes are selectable; non-leaf assembly/sub-assembly nodes are not selectable.
- 3D picking when parts overlap: pick the frontmost hit.
- Clicking empty space in 3D clears selection.
- When selection comes from 3D: auto-reveal in tree (expand parents + scroll into view).
- If a hidden part is clicked in the tree: still select it but keep it hidden (indicate hidden-selected).
- If a selected item becomes hidden: keep it selected and indicate it is hidden.
- Hidden objects are not pickable in 3D.

### Highlight + feedback

- 3D selected highlight style: match the existing highlight style used in the carbon-aware motor/gearbox assembly feature.
- Hover highlight: none.
- Tree hidden indication: eye/visibility icon per node + dim the label when hidden.
- No extra UI for hidden-selected beyond the tree indication.

### Visibility controls (hide/isolate)

- Controls live in both places:
  - Tree rows: per-node visibility toggles
  - Toolbar: actions that apply to current selection
- Visibility can be toggled on non-leaf nodes; hide/show on an assembly node applies to its subtree.
- Isolate behavior: toggle; turning isolate off restores the prior visibility state.
- Show all / reset visibility: unhide everything + clear isolation + keep current selection.

### Fit camera behavior

- Fit trigger: toolbar button only (explicit).
- Fit motion: smooth animated move.
- Fit target: keep current orbit target (do not retarget to selection).
- If there is no selection: fit to all currently visible geometry.

### Claude's Discretion

- Exact visuals and parameters of the highlight effect, as long as it matches the established carbon-aware assembly highlight pattern.
- Exact iconography/spacing for visibility controls, as long as per-node eye icon + label dimming is present.

</decisions>

<specifics>
## Specific Ideas

- Selected highlight should feel identical to the carbon-aware motor/gearbox assembly highlight behavior (no new highlight style invented for this phase).

</specifics>

<deferred>
## Deferred Ideas

- Search/filtering within the explorer tree (new capability; separate phase).
- Advanced selection sets / saved views (new capability; separate phase).

</deferred>

---

_Phase: 03-explorer-selection-workflow_
_Context gathered: 2026-02-07_
