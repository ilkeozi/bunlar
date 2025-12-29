import { memo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useThomsonStore } from '../state/useThomsonStore';
import { useTranslation } from '../../../../i18n/useTranslation';

export const ViewControls = memo(function ViewControls() {
  const view = useThomsonStore((state) => state.view);
  const updateView = useThomsonStore((state) => state.updateView);
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
          <Label htmlFor="positive-sphere" className="flex-1 text-sm text-muted-foreground">
            {t('controls.showPositiveSphere')}
          </Label>
          <Switch
            id="positive-sphere"
            checked={view.showPositiveSphere}
            onCheckedChange={(checked) => updateView({ showPositiveSphere: checked })}
          />
        </div>
        <div className="flex items-center justify-between gap-4">
          <Label htmlFor="cutaway-sphere" className="flex-1 text-sm text-muted-foreground">
            {t('controls.cutawaySphere')}
          </Label>
          <Switch
            id="cutaway-sphere"
            checked={view.cutawaySphere}
            onCheckedChange={(checked) => updateView({ cutawaySphere: checked })}
            disabled={!view.showPositiveSphere}
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
      </CardContent>
    </Card>
  );
});
