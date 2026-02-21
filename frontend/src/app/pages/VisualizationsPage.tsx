import { useMemo, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import bohrModelThumb from '@/assets/bohr-model-thumb.svg';
import daltonModelThumb from '@/assets/dalton-model-thumb.svg';
import rutherfordModelThumb from '@/assets/rutherford-model-thumb.svg';
import thomsonModelThumb from '@/assets/thomson-model-thumb.svg';
import gearboxThumb from '@/assets/gearbox.png';
import { Link } from 'react-router-dom';
import { useTranslation } from '../i18n/useTranslation';
import type { TranslationKey } from '../i18n/translations';

type VisualizationItem = {
  to: string;
  titleKey: TranslationKey;
  descriptionKey: TranslationKey;
  ctaKey: TranslationKey;
  image?: string;
};

type VisualizationSubject = 'chemistry' | 'climateTech';

type VisualizationFilter = 'all' | VisualizationSubject;

type SubjectFilterOption = {
  id: VisualizationFilter;
  labelKey: TranslationKey;
};

type VisualizationSubjectLabel = {
  id: VisualizationSubject;
  labelKey: TranslationKey;
};

const SUBJECT_FILTERS: SubjectFilterOption[] = [
  { id: 'all', labelKey: 'visualizations.filter.all' },
  { id: 'chemistry', labelKey: 'subjects.chemistry.title' },
  { id: 'climateTech', labelKey: 'subjects.climateTech.title' },
];

const SUBJECT_LABELS: VisualizationSubjectLabel[] = [
  { id: 'chemistry', labelKey: 'subjects.chemistry.title' },
  { id: 'climateTech', labelKey: 'subjects.climateTech.title' },
];

const VISUALIZATIONS: Array<VisualizationItem & { subject: VisualizationSubject }> = [
  {
    subject: 'climateTech',
    to: '/subjects/climate-tech/planetary-gearbox-assembly',
    titleKey: 'climateTech.modules.carbonAware.title',
    descriptionKey: 'climateTech.modules.carbonAware.description',
    ctaKey: 'climateTech.modules.carbonAware.cta',
    image: gearboxThumb,
  },
  {
    subject: 'climateTech',
    to: '/subjects/climate-tech/assembly-hierarchy-explorer',
    titleKey: 'climateTech.modules.assemblyViewer.title',
    descriptionKey: 'climateTech.modules.assemblyViewer.description',
    ctaKey: 'climateTech.modules.assemblyViewer.cta',
    image: gearboxThumb,
  },
  {
    subject: 'chemistry',
    to: '/subjects/chemistry/bohr-atom-model',
    titleKey: 'chemistry.modules.bohrModel.title',
    descriptionKey: 'chemistry.modules.bohrModel.description',
    ctaKey: 'chemistry.modules.bohrModel.cta',
    image: bohrModelThumb,
  },
  {
    subject: 'chemistry',
    to: '/subjects/chemistry/rutherford-atom-model',
    titleKey: 'chemistry.modules.rutherfordModel.title',
    descriptionKey: 'chemistry.modules.rutherfordModel.description',
    ctaKey: 'chemistry.modules.rutherfordModel.cta',
    image: rutherfordModelThumb,
  },
  {
    subject: 'chemistry',
    to: '/subjects/chemistry/thomson-atom-model',
    titleKey: 'chemistry.modules.thomsonModel.title',
    descriptionKey: 'chemistry.modules.thomsonModel.description',
    ctaKey: 'chemistry.modules.thomsonModel.cta',
    image: thomsonModelThumb,
  },
  {
    subject: 'chemistry',
    to: '/subjects/chemistry/dalton-atom-model',
    titleKey: 'chemistry.modules.daltonModel.title',
    descriptionKey: 'chemistry.modules.daltonModel.description',
    ctaKey: 'chemistry.modules.daltonModel.cta',
    image: daltonModelThumb,
  },
];

export function VisualizationsPage() {
  const { t } = useTranslation();
  const [activeFilter, setActiveFilter] = useState<VisualizationFilter>('all');

  const subjectLabelMap = useMemo(() => {
    return SUBJECT_LABELS.reduce<Record<VisualizationSubject, TranslationKey>>((acc, subject) => {
      acc[subject.id] = subject.labelKey;
      return acc;
    }, {} as Record<VisualizationSubject, TranslationKey>);
  }, []);

  const filteredItems = useMemo(() => {
    if (activeFilter === 'all') {
      return VISUALIZATIONS;
    }
    return VISUALIZATIONS.filter((item) => item.subject === activeFilter);
  }, [activeFilter]);

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          {t('visualizations.title')}
        </h2>
        <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
          {t('visualizations.subtitle')}
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-2">
        {SUBJECT_FILTERS.map((filter) => {
          const isActive = filter.id === activeFilter;
          return (
            <Button
              key={filter.id}
              type="button"
              variant="outline"
              size="sm"
              className={`rounded-full border-border/60 px-4 text-xs font-semibold uppercase tracking-wide ${
                isActive
                  ? 'border-primary/50 bg-primary/15 text-primary hover:bg-primary/20'
                  : 'hover:border-primary/40 hover:text-foreground'
              }`}
              onClick={() => setActiveFilter(filter.id)}
            >
              {t(filter.labelKey)}
            </Button>
          );
        })}
      </div>

      <div className="columns-1 gap-4 md:columns-2 xl:columns-3">
        {filteredItems.map((item) => (
          <div key={item.to} className="mb-4 break-inside-avoid">
            <Link to={item.to} className="group inline-block w-full">
              <Card className="transition group-hover:-translate-y-1 group-hover:border-primary/50 group-hover:shadow-2xl">
                <CardHeader>
                  <Badge variant="outline" className="w-fit border-border/60 text-[11px]">
                    {t(subjectLabelMap[item.subject])}
                  </Badge>
                  <CardTitle>{t(item.titleKey)}</CardTitle>
                  <CardDescription>{t(item.descriptionKey)}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="mb-4 overflow-hidden rounded-2xl border border-border/60 bg-background/80">
                    {item.image ? (
                      <img
                        src={item.image}
                        alt={t(item.titleKey)}
                        className="h-40 w-full object-cover"
                        loading="lazy"
                      />
                    ) : (
                      <div className="h-40 w-full bg-gradient-to-br from-primary/15 via-secondary/10 to-background/80" />
                    )}
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">
                    {t(item.ctaKey)}
                  </span>
                </CardContent>
              </Card>
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
