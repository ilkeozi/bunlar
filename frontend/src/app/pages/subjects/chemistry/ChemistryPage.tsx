import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import bohrModelThumb from '@/assets/bohr-model-thumb.svg';
import daltonModelThumb from '@/assets/dalton-model-thumb.svg';
import thomsonModelThumb from '@/assets/thomson-model-thumb.svg';
import rutherfordModelThumb from '@/assets/rutherford-model-thumb.svg';
import { Link } from 'react-router-dom';
import { IB_CHEMISTRY_SYLLABUS } from '../../../data/ib/chemistry';
import { useTranslation } from '../../../i18n/useTranslation';

export function ChemistryPage() {
  const { t } = useTranslation();
  const structureSection = IB_CHEMISTRY_SYLLABUS.sections.find((section) => section.id === 'structure-1');
  const bohrIbLabel = t('chemistry.modules.bohrModel.badge.ib');
  const bohrStructureLabel = structureSection?.label ?? t('chemistry.modules.bohrModel.badge.structure');
  const daltonIbLabel = t('chemistry.modules.daltonModel.badge.ib');
  const daltonStructureLabel = structureSection?.label ?? t('chemistry.modules.daltonModel.badge.structure');
  const thomsonIbLabel = t('chemistry.modules.thomsonModel.badge.ib');
  const thomsonStructureLabel = structureSection?.label ?? t('chemistry.modules.thomsonModel.badge.structure');
  const rutherfordIbLabel = t('chemistry.modules.rutherfordModel.badge.ib');
  const rutherfordStructureLabel = structureSection?.label ?? t('chemistry.modules.rutherfordModel.badge.structure');
  const structureTitle = structureSection?.title ?? 'Models of the particulate nature of matter';
  const bohrSubtopic =
    structureSection?.topics.find((topic) => topic.id === 'structure-1-2') ?? structureSection?.topics[0];
  const bohrSubtopicLabel = bohrSubtopic?.label ?? 'Structure 1.2';
  const bohrSubtopicTitle = bohrSubtopic?.title ?? 'The nuclear atom';
  const daltonSubtopic =
    structureSection?.topics.find((topic) => topic.id === 'structure-1-1') ?? structureSection?.topics[0];
  const daltonSubtopicLabel = daltonSubtopic?.label ?? 'Structure 1.1';
  const daltonSubtopicTitle = daltonSubtopic?.title ?? 'Introduction to the particulate nature of matter';
  const thomsonSubtopic =
    structureSection?.topics.find((topic) => topic.id === 'structure-1-2') ?? structureSection?.topics[0];
  const thomsonSubtopicLabel = thomsonSubtopic?.label ?? 'Structure 1.2';
  const thomsonSubtopicTitle = thomsonSubtopic?.title ?? 'The nuclear atom';
  const rutherfordSubtopic =
    structureSection?.topics.find((topic) => topic.id === 'structure-1-2') ?? structureSection?.topics[0];
  const rutherfordSubtopicLabel = rutherfordSubtopic?.label ?? 'Structure 1.2';
  const rutherfordSubtopicTitle = rutherfordSubtopic?.title ?? 'The nuclear atom';

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">{t('subjects.chemistry.title')}</h2>
        <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
          {t('subjects.chemistry.subtitle')}
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Link to="/subjects/chemistry/dalton-atom-model" className="group">
          <Card className="h-full transition group-hover:-translate-y-1 group-hover:border-primary/50 group-hover:shadow-2xl">
            <CardHeader>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge
                      variant="outline"
                      className="w-fit overflow-hidden border-border/60 bg-background/70 p-0 text-[11px] font-semibold"
                    >
                      <span className="bg-primary/20 px-2 py-0.5 text-primary">
                        {daltonIbLabel}
                      </span>
                      <span className="border-l border-border/60 px-2 py-0.5 text-foreground/80">
                        {daltonStructureLabel}
                      </span>
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <div className="space-y-1 text-xs">
                      <div className="inline-flex w-fit items-center rounded-full border border-border/60 bg-background/70 text-[11px] font-semibold uppercase tracking-wide">
                        <span className="bg-primary/20 px-2 py-0.5 text-primary">
                          {daltonIbLabel}
                        </span>
                      </div>
                      <div className="text-muted-foreground">
                        <span className="font-semibold text-foreground/80">{daltonStructureLabel}</span> — {structureTitle}
                      </div>
                      <div className="text-muted-foreground">
                        <span className="font-semibold text-foreground/80">{daltonSubtopicLabel}</span> — {daltonSubtopicTitle}
                      </div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <CardTitle>{t('chemistry.modules.daltonModel.title')}</CardTitle>
              <CardDescription>{t('chemistry.modules.daltonModel.description')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 overflow-hidden rounded-2xl border border-border/60 bg-background/80">
                <img
                  src={daltonModelThumb}
                  alt={t('chemistry.modules.daltonModel.title')}
                  className="h-40 w-full object-cover"
                  loading="lazy"
                />
              </div>
              <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">
                {t('chemistry.modules.daltonModel.cta')}
              </span>
            </CardContent>
          </Card>
        </Link>
        <Link to="/subjects/chemistry/thomson-atom-model" className="group">
          <Card className="h-full transition group-hover:-translate-y-1 group-hover:border-primary/50 group-hover:shadow-2xl">
            <CardHeader>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge
                      variant="outline"
                      className="w-fit overflow-hidden border-border/60 bg-background/70 p-0 text-[11px] font-semibold"
                    >
                      <span className="bg-primary/20 px-2 py-0.5 text-primary">
                        {thomsonIbLabel}
                      </span>
                      <span className="border-l border-border/60 px-2 py-0.5 text-foreground/80">
                        {thomsonStructureLabel}
                      </span>
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <div className="space-y-1 text-xs">
                      <div className="inline-flex w-fit items-center rounded-full border border-border/60 bg-background/70 text-[11px] font-semibold uppercase tracking-wide">
                        <span className="bg-primary/20 px-2 py-0.5 text-primary">
                          {thomsonIbLabel}
                        </span>
                      </div>
                      <div className="text-muted-foreground">
                        <span className="font-semibold text-foreground/80">{thomsonStructureLabel}</span> — {structureTitle}
                      </div>
                      <div className="text-muted-foreground">
                        <span className="font-semibold text-foreground/80">{thomsonSubtopicLabel}</span> — {thomsonSubtopicTitle}
                      </div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <CardTitle>{t('chemistry.modules.thomsonModel.title')}</CardTitle>
              <CardDescription>{t('chemistry.modules.thomsonModel.description')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 overflow-hidden rounded-2xl border border-border/60 bg-background/80">
                <img
                  src={thomsonModelThumb}
                  alt={t('chemistry.modules.thomsonModel.title')}
                  className="h-40 w-full object-cover"
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
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge
                      variant="outline"
                      className="w-fit overflow-hidden border-border/60 bg-background/70 p-0 text-[11px] font-semibold"
                    >
                      <span className="bg-primary/20 px-2 py-0.5 text-primary">
                        {rutherfordIbLabel}
                      </span>
                      <span className="border-l border-border/60 px-2 py-0.5 text-foreground/80">
                        {rutherfordStructureLabel}
                      </span>
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <div className="space-y-1 text-xs">
                      <div className="inline-flex w-fit items-center rounded-full border border-border/60 bg-background/70 text-[11px] font-semibold uppercase tracking-wide">
                        <span className="bg-primary/20 px-2 py-0.5 text-primary">
                          {rutherfordIbLabel}
                        </span>
                      </div>
                      <div className="text-muted-foreground">
                        <span className="font-semibold text-foreground/80">{rutherfordStructureLabel}</span> — {structureTitle}
                      </div>
                      <div className="text-muted-foreground">
                        <span className="font-semibold text-foreground/80">{rutherfordSubtopicLabel}</span> — {rutherfordSubtopicTitle}
                      </div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <CardTitle>{t('chemistry.modules.rutherfordModel.title')}</CardTitle>
              <CardDescription>{t('chemistry.modules.rutherfordModel.description')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 overflow-hidden rounded-2xl border border-border/60 bg-background/80">
                <img
                  src={rutherfordModelThumb}
                  alt={t('chemistry.modules.rutherfordModel.title')}
                  className="h-40 w-full object-cover"
                  loading="lazy"
                />
              </div>
              <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">
                {t('chemistry.modules.rutherfordModel.cta')}
              </span>
            </CardContent>
          </Card>
        </Link>
        <Link to="/subjects/chemistry/bohr-atom-model" className="group">
          <Card className="h-full transition group-hover:-translate-y-1 group-hover:border-primary/50 group-hover:shadow-2xl">
            <CardHeader>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge
                      variant="outline"
                      className="w-fit overflow-hidden border-border/60 bg-background/70 p-0 text-[11px] font-semibold"
                    >
                      <span className="bg-primary/20 px-2 py-0.5 text-primary">
                        {bohrIbLabel}
                      </span>
                      <span className="border-l border-border/60 px-2 py-0.5 text-foreground/80">
                        {bohrStructureLabel}
                      </span>
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <div className="space-y-1 text-xs">
                      <div className="inline-flex w-fit items-center rounded-full border border-border/60 bg-background/70 text-[11px] font-semibold uppercase tracking-wide">
                        <span className="bg-primary/20 px-2 py-0.5 text-primary">
                          {bohrIbLabel}
                        </span>
                      </div>
                      <div className="text-muted-foreground">
                        <span className="font-semibold text-foreground/80">{bohrStructureLabel}</span> — {structureTitle}
                      </div>
                      <div className="text-muted-foreground">
                        <span className="font-semibold text-foreground/80">{bohrSubtopicLabel}</span> — {bohrSubtopicTitle}
                      </div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <CardTitle>{t('chemistry.modules.bohrModel.title')}</CardTitle>
              <CardDescription>{t('chemistry.modules.bohrModel.description')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 overflow-hidden rounded-2xl border border-border/60 bg-background/80">
                <img
                  src={bohrModelThumb}
                  alt={t('chemistry.modules.bohrModel.title')}
                  className="h-40 w-full object-cover"
                  loading="lazy"
                />
              </div>
              <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">
                {t('chemistry.modules.bohrModel.cta')}
              </span>
            </CardContent>
          </Card>
        </Link>
        <Card className="border-dashed border-border/60 bg-background/60">
          <CardHeader>
            <CardTitle>{t('chemistry.modules.more.title')}</CardTitle>
            <CardDescription>{t('chemistry.modules.more.description')}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{t('chemistry.modules.more.note')}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
