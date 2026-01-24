import { Brain, Github, Linkedin, Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Link } from 'react-router-dom';
import { LanguageSelector } from './LanguageSelector';
import { useTranslation } from '../i18n/useTranslation';
import type { TranslationKey } from '../i18n/translations';

interface NavItem {
  labelKey: TranslationKey;
  to: string;
}

const NAV_ITEMS: NavItem[] = [
  { labelKey: 'nav.home', to: '/' },
  { labelKey: 'nav.visualizations', to: '/visualizations' },
  { labelKey: 'nav.tools', to: '/tools' },
  // { labelKey: 'nav.articles', to: '/articles' },
  // { labelKey: 'nav.about', to: '/about' },
];

export function SiteHeader() {
  const { t } = useTranslation();

  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-[1200px] items-center justify-between gap-4 px-6 py-4 sm:px-8 lg:px-10">
        <Link
          to="/"
          className="flex items-center gap-3 text-lg font-semibold tracking-tight text-foreground"
          aria-label={t('app.title')}
        >
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Brain className="h-5 w-5" aria-hidden="true" />
          </span>
          <span className="hidden sm:flex flex-col leading-tight">
            <span className="flex items-baseline gap-0.5 text-foreground">
              <span>{t('app.title')}</span>
              <span className="text-primary">.org</span>
            </span>
            <span className="text-xs font-medium tracking-[0.18em] text-muted-foreground">
              {t('app.subtitle')}
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-6 text-sm font-semibold text-muted-foreground md:flex">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="rounded-full px-3 py-1.5 transition-colors hover:bg-primary/10 hover:text-primary"
            >
              {t(item.labelKey)}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 md:flex">
            <a
              href="https://github.com/ilkeozi"
              target="_blank"
              rel="noreferrer"
              aria-label="GitHub"
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border/60 text-muted-foreground transition hover:border-primary/40 hover:text-foreground"
            >
              <Github className="h-4 w-4" />
            </a>
            <a
              href="https://www.linkedin.com/in/ilkeozi/"
              target="_blank"
              rel="noreferrer"
              aria-label="LinkedIn"
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border/60 text-muted-foreground transition hover:border-primary/40 hover:text-foreground"
            >
              <Linkedin className="h-4 w-4" />
            </a>
          </div>
          <div className="hidden md:block">
            <LanguageSelector variant="inline" />
          </div>

          <Sheet>
            <SheetTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="md:hidden"
                aria-label={t('nav.openMenu')}
              >
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
              <SheetContent side="left" className="w-[280px] border-border/60 bg-background/95">
                <SheetHeader className="text-left">
                  <SheetTitle className="flex items-baseline gap-1">
                    <span>{t('app.title')}</span>
                    <span className="text-primary">.org</span>
                  </SheetTitle>
                  <SheetDescription className="tracking-[0.14em]">
                    {t('app.subtitle')}
                  </SheetDescription>
                </SheetHeader>

              <div className="mt-6 flex flex-col gap-4">
                <nav className="space-y-1 text-sm font-semibold text-muted-foreground">
                  {NAV_ITEMS.map((item) => (
                    <SheetClose key={item.to} asChild>
                      <Link
                        to={item.to}
                        className="block rounded-xl border border-transparent px-3 py-2 transition-colors hover:border-primary/40 hover:bg-primary/10 hover:text-primary"
                      >
                        {t(item.labelKey)}
                      </Link>
                    </SheetClose>
                  ))}
                </nav>

                <div className="border-t border-border/60 pt-4">
                  <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground/80">
                    {t('app.language')}
                  </span>
                  <div className="mt-2">
                    <LanguageSelector showLabel={false} />
                  </div>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
