import { Html } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import { useRef, useState } from 'react';
import { useAssemblyExplorerStore } from '../state/useAssemblyExplorerStore';

type PerfStats = {
  fps: number;
  triangles: number;
  calls: number;
};

export function DevPerfOverlay() {
  const { gl } = useThree();

  const selectedNodeId = useAssemblyExplorerStore(
    (state) => state.selectedNodeId
  );
  const selectedOcafEntry = useAssemblyExplorerStore(
    (state) => state.selectedOcafEntry
  );
  const selectionSource = useAssemblyExplorerStore(
    (state) => state.selectionSource
  );
  const explicitHiddenCount = useAssemblyExplorerStore(
    (state) => state.explicitHiddenNodeIds.size
  );
  const isolateActive = useAssemblyExplorerStore(
    (state) => state.isolateActive
  );
  const meshesByOcafEntrySize = useAssemblyExplorerStore(
    (state) => state.meshesByOcafEntry?.size ?? 0
  );

  const [stats, setStats] = useState<PerfStats>({
    fps: 0,
    triangles: 0,
    calls: 0,
  });
  const framesRef = useRef(0);
  const secondsRef = useRef(0);
  const sinceUpdateRef = useRef(0);

  useFrame((_, delta) => {
    framesRef.current += 1;
    secondsRef.current += delta;
    sinceUpdateRef.current += delta;

    if (sinceUpdateRef.current < 0.25) {
      return;
    }

    const seconds = Math.max(secondsRef.current, 1e-6);
    const fps = framesRef.current / seconds;
    const { triangles, calls } = gl.info.render;

    setStats({ fps, triangles, calls });

    framesRef.current = 0;
    secondsRef.current = 0;
    sinceUpdateRef.current = 0;
  });

  return (
    <Html fullscreen style={{ pointerEvents: 'none' }}>
      <div
        style={{
          position: 'absolute',
          top: 10,
          left: 10,
          padding: '8px 10px',
          borderRadius: 10,
          background: 'rgba(10, 10, 10, 0.72)',
          border: '1px solid rgba(255, 255, 255, 0.14)',
          color: 'rgba(255, 255, 255, 0.92)',
          fontFamily:
            'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
          fontSize: 12,
          lineHeight: 1.25,
          letterSpacing: '0.01em',
          boxShadow: '0 12px 34px rgba(0, 0, 0, 0.35)',
          userSelect: 'none',
          WebkitUserSelect: 'none',
        }}
      >
        <div style={{ display: 'flex', gap: 10 }}>
          <div>
            <span style={{ opacity: 0.7 }}>FPS</span> {Math.round(stats.fps)}
          </div>
          <div>
            <span style={{ opacity: 0.7 }}>Tris</span>{' '}
            {stats.triangles.toLocaleString()}
          </div>
          <div>
            <span style={{ opacity: 0.7 }}>Calls</span>{' '}
            {stats.calls.toLocaleString()}
          </div>
        </div>

        <div style={{ marginTop: 8, opacity: 0.9 }}>
          <div>
            <span style={{ opacity: 0.7 }}>Sel</span> {selectedNodeId ?? 'null'}
          </div>
          <div>
            <span style={{ opacity: 0.7 }}>OCAF</span>{' '}
            {selectedOcafEntry ?? 'null'}
          </div>
          <div>
            <span style={{ opacity: 0.7 }}>Src</span> {selectionSource}
          </div>
          <div>
            <span style={{ opacity: 0.7 }}>Hidden</span> {explicitHiddenCount}{' '}
            <span style={{ opacity: 0.7 }}>Isolate</span>{' '}
            {String(isolateActive)}
          </div>
          <div>
            <span style={{ opacity: 0.7 }}>MeshIndex</span>{' '}
            {meshesByOcafEntrySize}
          </div>
        </div>
      </div>
    </Html>
  );
}
