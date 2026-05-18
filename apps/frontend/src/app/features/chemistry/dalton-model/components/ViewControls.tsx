import { memo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useDaltonStore } from '../state/useDaltonStore';
import { useTranslation } from '../../../../i18n/useTranslation';

export const ViewControls = memo(function ViewControls() {
  const view = useDaltonStore((state) => state.view);
  const updateView = useDaltonStore((state) => state.updateView);
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
