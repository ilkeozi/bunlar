import { Menu } from 'lucide-react';
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
import { LanguageSelector } from './LanguageSelector';
import { useTranslation } from '../i18n/useTranslation';

interface NavItem {
  label: string;
  href: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Overview', href: '#overview' },
  { label: 'Lessons', href: '#lessons' },
  { label: 'Blog', href: '#blog' },
  { label: 'About', href: '#about' },
  { label: 'Contact', href: '#contact' },
];

export function SiteHeader() {
  const { t } = useTranslation();

  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-[1200px] items-center justify-between gap-4 px-6 py-4 sm:px-8 lg:px-10">
        <a
          href="#overview"
          className="flex items-center gap-2 text-lg font-semibold tracking-tight text-primary"
          aria-label={t('app.title')}
        >
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
            SE
          </span>
          <span className="hidden sm:inline-flex text-foreground">{t('app.title')}</span>
        </a>

        <nav className="hidden items-center gap-6 text-sm font-semibold text-muted-foreground md:flex">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="rounded-full px-3 py-1.5 transition-colors hover:bg-primary/10 hover:text-primary"
            >
              {item.label}
            </a>
          ))}
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
                aria-label="Open navigation"
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
                    <SheetClose key={item.href} asChild>
                      <a
                        href={item.href}
                        className="block rounded-xl border border-transparent px-3 py-2 transition-colors hover:border-primary/40 hover:bg-primary/10 hover:text-primary"
                      >
                        {item.label}
                      </a>
                    </SheetClose>
                  ))}
                </nav>

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
