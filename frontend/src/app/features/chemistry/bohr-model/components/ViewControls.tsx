import { memo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useAtomStore } from '../state/useAtomStore';
import { useTranslation } from '../../../../i18n/useTranslation';

export const ViewControls = memo(function ViewControls() {
  const view = useAtomStore((state) => state.view);
  const updateView = useAtomStore((state) => state.updateView);
  const { t } = useTranslation();

  return (
    <Card>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <Label htmlFor="auto-rotate" className="flex-1 text-sm text-muted-foreground">
            {t('controls.autoRotate')}
          </Label>
          <Switch
            id="auto-rotate"
            checked={view.autoRotate}
            onCheckedChange={(checked) => updateView({ autoRotate: checked })}
          />
        </div>
        <div className="flex items-center justify-between gap-4">
          <Label htmlFor="freeze-motion" className="flex-1 text-sm text-muted-foreground">
            {t('controls.freezeMotion')}
          </Label>
          <Switch
            id="freeze-motion"
            checked={view.freezeMotion}
            onCheckedChange={(checked) => updateView({ freezeMotion: checked })}
          />
        </div>
        <div className="flex items-center justify-between gap-4">
          <Label htmlFor="rotate-atom" className="flex-1 text-sm text-muted-foreground">
            {t('controls.rotateAtom')}
          </Label>
          <Switch
            id="rotate-atom"
            checked={view.rotateAtom}
            onCheckedChange={(checked) => updateView({ rotateAtom: checked })}
          />
        </div>
        <div className="flex items-center justify-between gap-4">
          <Label htmlFor="tilted-orbits" className="flex-1 text-sm text-muted-foreground">
            {t('controls.tiltedOrbits')}
          </Label>
          <Switch
            id="tilted-orbits"
            checked={view.tiltedOrbits}
            onCheckedChange={(checked) => updateView({ tiltedOrbits: checked })}
          />
        </div>
        <div className="flex items-center justify-between gap-4">
          <Label htmlFor="show-trails" className="flex-1 text-sm text-muted-foreground">
            {t('controls.showTrails')}
          </Label>
          <Switch
            id="show-trails"
            checked={view.showElectronTrails}
            onCheckedChange={(checked) => updateView({ showElectronTrails: checked })}
          />
        </div>
      </CardContent>
    </Card>
  );
});
