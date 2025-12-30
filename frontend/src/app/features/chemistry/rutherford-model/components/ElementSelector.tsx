import { memo } from 'react';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ELEMENTS } from '../../../../data/elements';
import { useRutherfordStore } from '../state/useRutherfordStore';
import { useTranslation } from '../../../../i18n/useTranslation';

export const ElementSelector = memo(function ElementSelector() {
  const selectedSymbol = useRutherfordStore((state) => state.selectedSymbol);
  const selectElement = useRutherfordStore((state) => state.selectElement);
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor="element-select">{t('element.label')}</Label>
      <Select value={selectedSymbol} onValueChange={selectElement}>
        <SelectTrigger id="element-select" aria-label={t('element.label')}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent className="max-h-72">
          {ELEMENTS.map((item) => (
            <SelectItem key={item.symbol} value={item.symbol}>
              {item.atomicNumber}. {item.name} ({item.symbol})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
});
