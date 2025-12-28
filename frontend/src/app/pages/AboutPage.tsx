import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useTranslation } from '../i18n/useTranslation';

export function AboutPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t('about.title')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-muted-foreground">
          <p>{t('about.paragraph1')}</p>
          <p>{t('about.paragraph2')}</p>
        </CardContent>
      </Card>
    </div>
  );
}
