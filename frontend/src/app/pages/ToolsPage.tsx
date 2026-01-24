import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Link } from 'react-router-dom';
import { useTranslation } from '../i18n/useTranslation';

export function ToolsPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          {t('subjects.tools.title')}
        </h2>
        <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
          {t('subjects.tools.subtitle')}
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Link to="/tools/step-converter" className="group">
          <Card className="h-full transition group-hover:-translate-y-1 group-hover:border-primary/50 group-hover:shadow-2xl">
            <CardHeader>
              <Badge variant="outline" className="w-fit border-border/60 text-[11px]">
                {t('tools.stepConverter.badge')}
              </Badge>
              <CardTitle>{t('tools.stepConverter.title')}</CardTitle>
              <CardDescription>{t('tools.stepConverter.description')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 h-36 overflow-hidden rounded-2xl border border-border/60 bg-gradient-to-br from-primary/15 via-secondary/10 to-background/80" />
              <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">
                {t('tools.stepConverter.cta')}
              </span>
            </CardContent>
          </Card>
        </Link>
        <Link to="/tools/step-converter-browser" className="group">
          <Card className="h-full transition group-hover:-translate-y-1 group-hover:border-primary/50 group-hover:shadow-2xl">
            <CardHeader>
              <Badge variant="outline" className="w-fit border-border/60 text-[11px]">
                {t('tools.stepConverterBrowser.badge')}
              </Badge>
              <CardTitle>{t('tools.stepConverterBrowser.title')}</CardTitle>
              <CardDescription>
                {t('tools.stepConverterBrowser.description')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 h-36 overflow-hidden rounded-2xl border border-border/60 bg-gradient-to-br from-primary/10 via-secondary/10 to-background/80" />
              <span className="text-xs font-semibold uppercase tracking-wide text-primary/80">
                {t('tools.stepConverterBrowser.cta')}
              </span>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
