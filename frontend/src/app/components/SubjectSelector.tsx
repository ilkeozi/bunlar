import { SUBJECTS, useLearningStore } from '../state/useLearningStore';
import { useTranslation } from '../i18n/useTranslation';
import { cn } from '@/lib/utils';

export function SubjectSelector() {
  const subject = useLearningStore((state) => state.subject);
  const setSubject = useLearningStore((state) => state.setSubject);
  const { t } = useTranslation();

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {SUBJECTS.map((item) => {
        const isActive = subject === item.id;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => setSubject(item.id)}
            className={cn(
              'group rounded-2xl border border-border/60 bg-background/60 p-4 text-left transition-all hover:border-primary/40 hover:bg-background/80 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background',
              isActive && 'border-primary bg-primary/10 shadow-lg shadow-primary/20 backdrop-blur'
            )}
          >
            <span className="block text-lg font-semibold text-foreground sm:text-xl">
              {t(item.titleKey)}
            </span>
            <span className="mt-2 block text-sm text-muted-foreground">
              {t(item.descriptionKey)}
            </span>
          </button>
        );
      })}
    </div>
  );
}
