import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { TranslationKey } from '../i18n/translations';
import { useTranslation } from '../i18n/useTranslation';

interface SubjectPlaceholderPageProps {
  titleKey: TranslationKey;
  descriptionKey: TranslationKey;
}

export function SubjectPlaceholderPage({ titleKey, descriptionKey }: SubjectPlaceholderPageProps) {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t(titleKey)}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{t(descriptionKey)}</p>
        </CardContent>
      </Card>
    </div>
  );
}
