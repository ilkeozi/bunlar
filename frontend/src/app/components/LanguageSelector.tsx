import { SUPPORTED_LANGUAGES, useLearningStore } from '../state/useLearningStore';
import type { SupportedLanguage } from '../i18n/translations';
import { useTranslation } from '../i18n/useTranslation';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const LANGUAGE_LABELS: Record<SupportedLanguage, string> = {
  en: 'English',
  tr: 'Turkce',
};

export function LanguageSelector() {
  const { language, t } = useTranslation();
  const setLanguage = useLearningStore((state) => state.setLanguage);

  return (
    <div className="flex min-w-[200px] flex-col gap-2">
      <Label htmlFor="language-select" className="text-sm text-muted-foreground">
        {t('app.language')}
      </Label>
      <Select value={language} onValueChange={(value) => setLanguage(value as SupportedLanguage)}>
        <SelectTrigger id="language-select">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {SUPPORTED_LANGUAGES.map((item) => (
            <SelectItem key={item} value={item}>
              {LANGUAGE_LABELS[item]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
