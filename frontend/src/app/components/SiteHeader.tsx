import { ChevronDown, Menu } from 'lucide-react';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
  { labelKey: 'nav.articles', to: '/articles' },
  { labelKey: 'nav.about', to: '/about' },
];

const SUBJECT_ITEMS: NavItem[] = [
  { labelKey: 'subjects.chemistry.title', to: '/subjects/chemistry' },
  { labelKey: 'subjects.climateTech.title', to: '/subjects/climate-tech' },
  { labelKey: 'subjects.biology.title', to: '/subjects/biology' },
  { labelKey: 'subjects.physics.title', to: '/subjects/physics' },
  { labelKey: 'subjects.mathematics.title', to: '/subjects/mathematics' },
];

export function SiteHeader() {
  const { t } = useTranslation();

  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-[1200px] items-center justify-between gap-4 px-6 py-4 sm:px-8 lg:px-10">
        <Link
          to="/"
          className="flex items-center gap-3 text-lg font-semibold tracking-tight text-primary"
          aria-label={t('app.title')}
        >
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
            B
          </span>
          <span className="hidden sm:flex flex-col leading-tight">
            <span className="text-foreground">{t('app.title')}</span>
            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {t('app.subtitle')}
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-6 text-sm font-semibold text-muted-foreground md:flex">
          <Link
            to="/"
            className="rounded-full px-3 py-1.5 transition-colors hover:bg-primary/10 hover:text-primary"
          >
            {t('nav.home')}
          </Link>
          <Link
            to="/articles"
            className="rounded-full px-3 py-1.5 transition-colors hover:bg-primary/10 hover:text-primary"
          >
            {t('nav.articles')}
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                className="h-9 rounded-full px-3 text-sm font-semibold text-muted-foreground hover:bg-primary/10 hover:text-primary"
              >
                {t('nav.visualizations')}
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              <DropdownMenuLabel>{t('nav.visualizations')}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {SUBJECT_ITEMS.map((item) => (
                <DropdownMenuItem key={item.to} asChild className="cursor-pointer">
                  <Link to={item.to}>{t(item.labelKey)}</Link>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          <Link
            to="/about"
            className="rounded-full px-3 py-1.5 transition-colors hover:bg-primary/10 hover:text-primary"
          >
            {t('nav.about')}
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <div className="hidden md:block">
            <LanguageSelector />
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
                <SheetTitle>{t('app.title')}</SheetTitle>
                <SheetDescription>{t('app.subtitle')}</SheetDescription>
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

                <div className="space-y-1">
                  <span className="px-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground/80">
                    {t('nav.visualizations')}
                  </span>
                  {SUBJECT_ITEMS.map((item) => (
                    <SheetClose key={item.to} asChild>
                      <Link
                        to={item.to}
                        className="block rounded-xl border border-transparent px-3 py-2 text-sm font-semibold text-muted-foreground transition-colors hover:border-primary/40 hover:bg-primary/10 hover:text-primary"
                      >
                        {t(item.labelKey)}
                      </Link>
                    </SheetClose>
                  ))}
                </div>

                <div className="border-t border-border/60 pt-4">
                  <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground/80">
                    {t('app.language')}
                  </span>
                  <div className="mt-2">
                    <LanguageSelector />
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
