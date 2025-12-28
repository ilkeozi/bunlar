import { useTranslation } from '../i18n/useTranslation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function HomePage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{t('app.title')}</h1>
        <p className="max-w-3xl text-base text-muted-foreground sm:text-lg">{t('app.subtitle')}</p>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>{t('home.start.title')}</CardTitle>
          <CardDescription>{t('home.start.description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {t('home.start.note')}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
