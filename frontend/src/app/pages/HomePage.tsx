import { useTranslation } from '../i18n/useTranslation';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Link } from 'react-router-dom';
import gearboxThumb from '@/assets/gearbox.png';
import bohrModelThumb from '@/assets/bohr-model-thumb.svg';
import thomsonModelThumb from '@/assets/thomson-model-thumb.svg';
import rutherfordModelThumb from '@/assets/rutherford-model-thumb.svg';

export function HomePage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-8">
      <Link to="/subjects/climate-tech/planetary-gearbox-assembly" className="group block">
        <Card className="overflow-hidden transition group-hover:-translate-y-1 group-hover:border-primary/50 group-hover:shadow-2xl">
          <div className="relative">
            <img
              src={gearboxThumb}
              alt={t('climateTech.modules.carbonAware.title')}
              className="h-56 w-full object-cover sm:h-64"
              loading="lazy"
            />
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-background/95 via-background/70 to-transparent" />
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-background/90 via-background/40 to-transparent" />
            <div className="absolute left-6 top-6 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-primary">
              {t('home.featured.title')}
            </div>
          </div>
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

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <h2 className="text-xl font-semibold tracking-tight sm:text-2xl">
              {t('visualizations.title')}
            </h2>
            <p className="text-sm text-muted-foreground sm:text-base">
              {t('visualizations.subtitle')}
            </p>
          </div>
          <Link
            to="/visualizations"
            className="text-xs font-semibold uppercase tracking-wide text-primary/80"
          >
            {t('nav.visualizations')}
          </Link>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <Link to="/subjects/chemistry/bohr-atom-model" className="group">
            <Card className="h-full transition group-hover:-translate-y-1 group-hover:border-primary/50 group-hover:shadow-2xl">
              <CardHeader>
                <Badge variant="outline" className="w-fit border-border/60 text-[11px]">
                  {t('subjects.chemistry.title')}
                </Badge>
                <CardTitle>{t('chemistry.modules.bohrModel.title')}</CardTitle>
                <CardDescription>{t('chemistry.modules.bohrModel.description')}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-4 overflow-hidden rounded-2xl border border-border/60 bg-background/80">
                  <img
                    src={bohrModelThumb}
                    alt={t('chemistry.modules.bohrModel.title')}
                    className="h-36 w-full object-contain p-2"
                    loading="lazy"
                  />
                </div>
                <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">
                  {t('chemistry.modules.bohrModel.cta')}
                </span>
              </CardContent>
            </Card>
          </Link>

          <Link to="/subjects/chemistry/thomson-atom-model" className="group">
            <Card className="h-full transition group-hover:-translate-y-1 group-hover:border-primary/50 group-hover:shadow-2xl">
              <CardHeader>
                <Badge variant="outline" className="w-fit border-border/60 text-[11px]">
                  {t('subjects.chemistry.title')}
                </Badge>
                <CardTitle>{t('chemistry.modules.thomsonModel.title')}</CardTitle>
                <CardDescription>{t('chemistry.modules.thomsonModel.description')}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-4 overflow-hidden rounded-2xl border border-border/60 bg-background/80">
                  <img
                    src={thomsonModelThumb}
                    alt={t('chemistry.modules.thomsonModel.title')}
                    className="h-36 w-full object-contain p-2"
                    loading="lazy"
                  />
                </div>
                <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">
                  {t('chemistry.modules.thomsonModel.cta')}
                </span>
              </CardContent>
            </Card>
          </Link>

          <Link to="/subjects/chemistry/rutherford-atom-model" className="group">
            <Card className="h-full transition group-hover:-translate-y-1 group-hover:border-primary/50 group-hover:shadow-2xl">
              <CardHeader>
                <Badge variant="outline" className="w-fit border-border/60 text-[11px]">
                  {t('subjects.chemistry.title')}
                </Badge>
                <CardTitle>{t('chemistry.modules.rutherfordModel.title')}</CardTitle>
                <CardDescription>{t('chemistry.modules.rutherfordModel.description')}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-4 overflow-hidden rounded-2xl border border-border/60 bg-background/80">
                  <img
                    src={rutherfordModelThumb}
                    alt={t('chemistry.modules.rutherfordModel.title')}
                    className="h-36 w-full object-contain p-2"
                    loading="lazy"
                  />
                </div>
                <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">
                  {t('chemistry.modules.rutherfordModel.cta')}
                </span>
              </CardContent>
            </Card>
          </Link>
        </div>
      </section>
    </div>
  );
}
