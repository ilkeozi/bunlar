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
  pcfOverlayMode: PcfOverlayMode;
  onPcfOverlayModeChange: (value: PcfOverlayMode) => void;
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
  pcfOverlayMode,
  onPcfOverlayModeChange,
  explode,
  onExplodeChange,
  partsCount,
  onResetView,
}: ViewControlsProps) {
  const { t } = useTranslation();
  const showDebugMaterials = false;

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
        {showDebugMaterials && (
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
        )}
        <div className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="pcf-overlay-mode" className="text-sm text-muted-foreground">
              {t('controls.pcfOverlay')}
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
                <SelectItem value="none">{t('controls.pcfOverlayNone')}</SelectItem>
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
        </div>
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
