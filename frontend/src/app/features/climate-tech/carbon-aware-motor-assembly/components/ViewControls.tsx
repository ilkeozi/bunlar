import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import type { PcfOverlayMode } from '../types';
import { useTranslation } from '../../../../i18n/useTranslation';

interface ViewControlsProps {
  autoRotate: boolean;
  onAutoRotateChange: (value: boolean) => void;
  debugMaterials: boolean;
  onDebugMaterialsChange: (value: boolean) => void;
  pcfOverlay: boolean;
  onPcfOverlayChange: (value: boolean) => void;
  pcfOverlayMode: PcfOverlayMode;
  onPcfOverlayModeChange: (value: PcfOverlayMode) => void;
  pcfMaxByMode: Record<PcfOverlayMode, number>;
  explode: number;
  onExplodeChange: (value: number) => void;
  partsCount: number | null;
  onResetView: () => void;
}

export function ViewControls({
  autoRotate,
  onAutoRotateChange,
  debugMaterials,
  onDebugMaterialsChange,
  pcfOverlay,
  onPcfOverlayChange,
  pcfOverlayMode,
  onPcfOverlayModeChange,
  pcfMaxByMode,
  explode,
  onExplodeChange,
  partsCount,
  onResetView,
}: ViewControlsProps) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('controls.viewTitle')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <Label
            htmlFor="orbit-auto-rotate"
            className="flex-1 text-sm text-muted-foreground"
          >
            {t('controls.autoRotate')}
          </Label>
          <Switch
            id="orbit-auto-rotate"
            checked={autoRotate}
            onCheckedChange={onAutoRotateChange}
          />
        </div>
        <div className="flex items-center justify-between gap-4">
          <Label
            htmlFor="debug-materials"
            className="flex-1 text-sm text-muted-foreground"
          >
            {t('controls.debugMaterials')}
          </Label>
          <Switch
            id="debug-materials"
            checked={debugMaterials}
            onCheckedChange={onDebugMaterialsChange}
          />
        </div>
        <div className="flex items-center justify-between gap-4">
          <Label
            htmlFor="pcf-overlay"
            className="flex-1 text-sm text-muted-foreground"
          >
            {t('controls.pcfOverlay')}
          </Label>
          <Switch
            id="pcf-overlay"
            checked={pcfOverlay}
            onCheckedChange={onPcfOverlayChange}
          />
        </div>
        {pcfOverlay && (
          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="pcf-overlay-mode" className="text-sm text-muted-foreground">
                {t('controls.pcfOverlayMode')}
              </Label>
              <Select
                value={pcfOverlayMode}
                onValueChange={(value) =>
                  onPcfOverlayModeChange(value as PcfOverlayMode)
                }
              >
                <SelectTrigger id="pcf-overlay-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="total">{t('controls.pcfOverlayTotal')}</SelectItem>
                  <SelectItem value="material">
                    {t('controls.pcfOverlayMaterial')}
                  </SelectItem>
                  <SelectItem value="manufacturing">
                    {t('controls.pcfOverlayManufacturing')}
                  </SelectItem>
                  <SelectItem value="transport">
                    {t('controls.pcfOverlayTransport')}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="rounded-lg border border-border/60 bg-muted/20 p-3">
              <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                <span>{t('controls.pcfLegendLow')}</span>
                <span>
                  {t('controls.pcfLegendHigh')} {pcfMaxByMode[pcfOverlayMode].toFixed(2)}
                </span>
              </div>
              <div
                className="mt-2 h-2 w-full rounded-full"
                style={{
                  background:
                    'linear-gradient(90deg, #2563eb 0%, #22c55e 45%, #f59e0b 70%, #ef4444 100%)',
                }}
              />
              <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-sky-500" />
                  {t('controls.pcfLegendMaterial')}
                </span>
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-amber-400" />
                  {t('controls.pcfLegendManufacturing')}
                </span>
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  {t('controls.pcfLegendTransport')}
                </span>
              </div>
            </div>
          </div>
        )}
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <Label
              htmlFor="explode-view"
              className="flex-1 text-sm text-muted-foreground"
            >
              {t('controls.explode')}
            </Label>
            <span className="text-xs text-muted-foreground">
              {Math.round(explode * 100)}%
            </span>
          </div>
          <input
            id="explode-view"
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={explode}
            onChange={(event) => onExplodeChange(Number(event.target.value))}
            className="h-2 w-full cursor-pointer appearance-none rounded-full bg-muted/40 accent-sky-400"
          />
          {partsCount !== null && (
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{t('controls.partsDetected')}</span>
              <span>{partsCount}</span>
            </div>
          )}
          {partsCount !== null && partsCount <= 1 && (
            <p className="text-xs text-muted-foreground">
              {t('controls.explodeHintSingle')}
            </p>
          )}
        </div>
        <Button variant="secondary" className="w-full" onClick={onResetView}>
          {t('controls.resetView')}
        </Button>
      </CardContent>
    </Card>
  );
}
