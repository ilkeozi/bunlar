import { useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Html, Line } from '@react-three/drei';
import { Vector3, type Group, type Mesh } from 'three';
import type { Line2 } from 'three-stdlib';
import { useTranslation } from '../../../../i18n/useTranslation';
import type { SelectedPart } from '../types';

interface PartTooltipProps {
  selection: SelectedPart | null;
  showEmissions: boolean;
}

export function PartTooltip({ selection, showEmissions }: PartTooltipProps) {
  const { t } = useTranslation();
  const { camera, size } = useThree();
  const groupRef = useRef<Group | null>(null);
  const htmlRef = useRef<HTMLDivElement | null>(null);
  const tooltipSize = useRef({ width: 240, height: 160 });
  const lineRef = useRef<Line2 | null>(null);
  const linePoints = useRef<ReadonlyArray<[number, number, number]>>([
    [0, 0, 0],
    [0, 0, 0],
  ]);
  const anchorRef = useRef<Mesh | null>(null);
  const linePositions = useRef(new Float32Array(6));
  const lastLinePositions = useRef(new Float32Array(6));
  const meshPosition = useRef(new Vector3());
  const cameraForward = useRef(new Vector3());
  const cameraRight = useRef(new Vector3());
  const cameraUp = useRef(new Vector3());
  const screenPosition = useRef(new Vector3());
  const tooltipPosition = useRef(new Vector3());

  useFrame(() => {
    if (!selection?.mesh || !groupRef.current) {
      return;
    }
    if (htmlRef.current) {
      tooltipSize.current.width =
        htmlRef.current.offsetWidth || tooltipSize.current.width;
      tooltipSize.current.height =
        htmlRef.current.offsetHeight || tooltipSize.current.height;
    }
    selection.mesh.getWorldPosition(meshPosition.current);
    camera.getWorldDirection(cameraForward.current);
    cameraUp.current.copy(camera.up).normalize();
    cameraRight.current
      .crossVectors(cameraForward.current, cameraUp.current)
      .normalize();
    screenPosition.current.copy(meshPosition.current).project(camera);
    const horizontalSign = screenPosition.current.x >= 0 ? -1 : 1;
    tooltipPosition.current.copy(meshPosition.current);
    tooltipPosition.current.addScaledVector(
      cameraRight.current,
      0.55 * horizontalSign
    );
    tooltipPosition.current.addScaledVector(cameraUp.current, 0.28);
    tooltipPosition.current.addScaledVector(cameraForward.current, -0.18);
    screenPosition.current.copy(tooltipPosition.current).project(camera);
    const screenX = (screenPosition.current.x * 0.5 + 0.5) * size.width;
    const screenY = (-screenPosition.current.y * 0.5 + 0.5) * size.height;
    const halfWidth = tooltipSize.current.width / 2;
    const halfHeight = tooltipSize.current.height / 2;
    const margin = 12;
    const minX = margin + halfWidth;
    const maxX = size.width - margin - halfWidth;
    const minY = margin + halfHeight;
    const maxY = size.height - margin - halfHeight;
    const clampedX =
      minX > maxX ? size.width / 2 : Math.min(Math.max(screenX, minX), maxX);
    const clampedY =
      minY > maxY ? size.height / 2 : Math.min(Math.max(screenY, minY), maxY);

    if (clampedX !== screenX || clampedY !== screenY) {
      screenPosition.current.x = (clampedX / size.width) * 2 - 1;
      screenPosition.current.y = -(clampedY / size.height) * 2 + 1;
      tooltipPosition.current.copy(screenPosition.current).unproject(camera);
    }

    groupRef.current.position.copy(tooltipPosition.current);

    linePositions.current[0] = tooltipPosition.current.x;
    linePositions.current[1] = tooltipPosition.current.y;
    linePositions.current[2] = tooltipPosition.current.z;
    linePositions.current[3] = meshPosition.current.x;
    linePositions.current[4] = meshPosition.current.y;
    linePositions.current[5] = meshPosition.current.z;
    if (lineRef.current) {
      const previous = lastLinePositions.current;
      let changed = false;
      for (let i = 0; i < linePositions.current.length; i += 1) {
        if (Math.abs(linePositions.current[i] - previous[i]) > 1e-4) {
          changed = true;
          break;
        }
      }
      if (changed) {
        lineRef.current.geometry.setPositions(linePositions.current);
        lineRef.current.geometry.computeBoundingSphere();
        previous.set(linePositions.current);
      }
    }

    if (anchorRef.current) {
      anchorRef.current.position.copy(meshPosition.current);
    }
  });

  if (!selection) {
    return null;
  }

  const breakdown = selection.meta?.pcf?.breakdown;
  const formatValue = (value?: number) =>
    typeof value === 'number' ? value.toFixed(2) : '--';
  const massEstimate = selection.meta?.pcf?.mass_kg_est;
  const formatMass = (value?: number) =>
    typeof value === 'number' ? value.toFixed(2) : '--';
  const name =
    selection.meta?.label ??
    selection.meta?.name ??
    selection.meta?.key ??
    selection.mesh.name ??
    t('climateTech.tooltip.unknownPart');
  const material =
    selection.meta?.material ??
    selection.meta?.material_guess ??
    t('climateTech.tooltip.unknownValue');
  const category =
    selection.meta?.category ?? t('climateTech.tooltip.unknownValue');

  const renderName = (value: string) => {
    const normalized = value.replace(/\s+/g, ' ').trim();
    if (normalized.length <= 44) {
      return normalized;
    }
    return `${normalized.slice(0, 41)}...`;
  };

  return (
    <>
      <Line
        ref={lineRef}
        points={linePoints.current}
        color="#7dd3fc"
        lineWidth={1}
        transparent
        opacity={0.7}
        depthTest={false}
        raycast={() => {}}
      />
      <mesh ref={anchorRef} raycast={() => {}}>
        <sphereGeometry args={[0.02, 12, 12]} />
        <meshBasicMaterial
          color="#7dd3fc"
          transparent
          opacity={0.9}
          depthTest={false}
        />
      </mesh>
      <group ref={groupRef}>
        <Html
          center
          ref={htmlRef}
          style={{ pointerEvents: 'none' }}
          className="w-[240px] max-w-[240px] rounded-lg border border-slate-700/60 bg-slate-950/80 px-3 py-3 text-[11px] text-slate-100 shadow-lg backdrop-blur"
        >
          <div className="text-xs font-semibold leading-snug text-slate-50">
            {renderName(name)}
          </div>
          <div className="mt-1 text-[11px] text-slate-300">
            {t('climateTech.tooltip.materialLabel')}:{' '}
            <span className="text-slate-100">{material}</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-300">
            {t('climateTech.tooltip.categoryLabel')}:{' '}
            <span className="text-slate-100">{category}</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-300">
            {t('climateTech.tooltip.massLabel')}:{' '}
            <span className="text-slate-100">
              {formatMass(massEstimate)} {t('units.kg')}
            </span>
          </div>
          {showEmissions && (
            <>
              <div className="mt-3 text-[10px] uppercase tracking-wide text-slate-400">
                {t('climateTech.tooltip.co2eBreakdown')}
              </div>
              <div className="mt-1 grid grid-cols-[minmax(90px,1fr)_minmax(110px,auto)] gap-x-3 gap-y-1 text-[11px] tabular-nums">
                <div className="text-slate-400">
                  {t('controls.pcfOverlayMaterial')}
                </div>
                <div className="text-slate-100 text-right whitespace-nowrap">
                  {formatValue(breakdown?.material)} {t('controls.pcfLegendUnit')}
                </div>
                <div className="text-slate-400">
                  {t('controls.pcfOverlayManufacturing')}
                </div>
                <div className="text-slate-100 text-right whitespace-nowrap">
                  {formatValue(breakdown?.manufacturing)}{' '}
                  {t('controls.pcfLegendUnit')}
                </div>
                <div className="text-slate-400">
                  {t('controls.pcfOverlayTransport')}
                </div>
                <div className="text-slate-100 text-right whitespace-nowrap">
                  {formatValue(breakdown?.transport)}{' '}
                  {t('controls.pcfLegendUnit')}
                </div>
              </div>
            </>
          )}
        </Html>
      </group>
    </>
  );
}
