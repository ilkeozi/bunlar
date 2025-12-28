import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import atomVisualizerThumb from '@/assets/atomic-visualizer-thumb.svg';
import { Link } from 'react-router-dom';
import { IB_CHEMISTRY_SYLLABUS } from '../../../data/ib/chemistry';
import { useTranslation } from '../../../i18n/useTranslation';

export function ChemistryPage() {
  const { t } = useTranslation();
  const structureSection = IB_CHEMISTRY_SYLLABUS.sections.find((section) => section.id === 'structure-1');
  const ibLabel = t('chemistry.modules.atomicVisualizer.badge.ib');
  const structureLabel = structureSection?.label ?? t('chemistry.modules.atomicVisualizer.badge.structure');
  const structureTitle = structureSection?.title ?? 'Models of the particulate nature of matter';
  const subtopic =
    structureSection?.topics.find((topic) => topic.id === 'structure-1-2') ?? structureSection?.topics[0];
  const subtopicLabel = subtopic?.label ?? 'Structure 1.2';
  const subtopicTitle = subtopic?.title ?? 'The nuclear atom';

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">{t('subjects.chemistry.title')}</h2>
        <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
          {t('subjects.chemistry.subtitle')}
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Link to="/subjects/chemistry/atom-visualizer" className="group">
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
                        {ibLabel}
                      </span>
                      <span className="border-l border-border/60 px-2 py-0.5 text-foreground/80">
                        {structureLabel}
                      </span>
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <div className="space-y-1 text-xs">
                      <div className="inline-flex w-fit items-center rounded-full border border-border/60 bg-background/70 text-[11px] font-semibold uppercase tracking-wide">
                        <span className="bg-primary/20 px-2 py-0.5 text-primary">
                          {ibLabel}
                        </span>
                      </div>
                      <div className="text-muted-foreground">
                        <span className="font-semibold text-foreground/80">{structureLabel}</span> — {structureTitle}
                      </div>
                      <div className="text-muted-foreground">
                        <span className="font-semibold text-foreground/80">{subtopicLabel}</span> — {subtopicTitle}
                      </div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <CardTitle>{t('chemistry.modules.atomicVisualizer.title')}</CardTitle>
              <CardDescription>{t('chemistry.modules.atomicVisualizer.description')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 overflow-hidden rounded-2xl border border-border/60 bg-background/80">
                <img
                  src={atomVisualizerThumb}
                  alt={t('chemistry.modules.atomicVisualizer.title')}
                  className="h-40 w-full object-cover"
                  loading="lazy"
                />
              </div>
              <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">
                {t('chemistry.modules.atomicVisualizer.cta')}
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
