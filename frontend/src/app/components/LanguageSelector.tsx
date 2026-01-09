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

interface LanguageSelectorProps {
  variant?: 'stacked' | 'inline';
  showLabel?: boolean;
  className?: string;
}

const LANGUAGE_LABELS: Record<SupportedLanguage, string> = {
  en: 'English',
  tr: 'Turkce',
};

export function LanguageSelector({
  variant = 'stacked',
  showLabel = true,
  className,
}: LanguageSelectorProps) {
  const { language, t } = useTranslation();
  const setLanguage = useLearningStore((state) => state.setLanguage);
  const isInline = variant === 'inline';
  const containerClassName = [
    'flex',
    isInline ? 'items-center gap-2' : 'min-w-[200px] flex-col gap-2',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={containerClassName}>
      {showLabel && (
        <Label
          htmlFor="language-select"
          className={
            isInline
              ? 'text-xs font-semibold uppercase tracking-wide text-muted-foreground/80'
              : 'text-sm text-muted-foreground'
          }
        >
          {t('app.language')}
        </Label>
      )}
      <Select value={language} onValueChange={(value) => setLanguage(value as SupportedLanguage)}>
        <SelectTrigger
          id="language-select"
          className={isInline ? 'h-9 min-w-[140px]' : undefined}
          aria-label={showLabel ? undefined : t('app.language')}
        >
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
