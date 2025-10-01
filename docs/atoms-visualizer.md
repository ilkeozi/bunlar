# Atomic Explorer Frontend Notes

This document captures the principles we agreed to follow while iterating on the 3D atom visualiser.

## Architecture guardrails

- **Declarative 3D** – we use `@react-three/fiber`/`drei` so the scene graph lives in React state and follows normal component lifecycles. Avoid creating imperative Three.js singletons in components; prefer hooks and declarative primitives.
- **State as a service** – global UI + simulation state is centralised in a lightweight Zustand store (`useAtomStore`). New timeline/interaction modules should subscribe through selectors rather than prop drilling.
- **Pure data modules** – numerical helpers and element metadata live in `app/data` and `app/utils`. These modules stay framework agnostic to support reuse in other runtimes (web workers, future native clients, etc.).
- **Composable visuals** – the visualiser is split into focused components (`AtomSystem`, `Nucleus`, `ElectronCloud`, `SoftLightRig`) so future features like decay animations or multi-atom scenes can slot in without rewriting the renderer.

## Visual direction

- **Physically believable shading** – prefer `meshPhysicalMaterial` with tuned roughness/clearcoat to fake subsurface scattering over flat lambert shading.
- **Readable energy levels** – shell radii and colours encode occupancy; keep electron trails optional and driven by store settings.
- **Atmospheric lighting** – stage lighting is handled by `SoftLightRig` (directional + hemisphere + lightformer). Post-processing is avoided for now to remain compatible with React 19 / R3F v9.

## Scaling forward

- When modelling interactions (bonding, decay, forces), create new slices in the Zustand store (`interactions`, `timeline`) and keep render-only derived state (e.g. interpolated trajectories) inside R3F hooks.
- Heavy physics should run off the main thread. Consider a worker that emits per-frame particle transforms; the renderer can consume them via `useFrame`.
- Keep docs updated whenever we alter visual conventions or store shape so future prompts can build on the same assumptions.
