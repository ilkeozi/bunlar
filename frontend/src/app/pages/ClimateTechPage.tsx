import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Link } from 'react-router-dom';
import { useTranslation } from '../i18n/useTranslation';

export function ClimateTechPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          {t('subjects.climateTech.title')}
        </h2>
        <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
          {t('subjects.climateTech.subtitle')}
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Link to="/subjects/climate-tech/planetary-gearbox-assembly" className="group">
          <Card className="h-full transition group-hover:-translate-y-1 group-hover:border-primary/50 group-hover:shadow-2xl">
            <CardHeader>
              <CardTitle>{t('climateTech.modules.carbonAware.title')}</CardTitle>
              <CardDescription>{t('climateTech.modules.carbonAware.description')}</CardDescription>
            </CardHeader>
            <CardContent>
              <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">
                {t('climateTech.modules.carbonAware.cta')}
              </span>
            </CardContent>
          </Card>
        </Link>
        <Card className="border-dashed border-border/60 bg-background/60">
          <CardHeader>
            <CardTitle>{t('modules.more.title')}</CardTitle>
            <CardDescription>{t('modules.more.description')}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{t('modules.more.note')}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
