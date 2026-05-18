import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

type LoadingSpinnerProps = HTMLAttributes<HTMLSpanElement> & {
  size?: 'xs' | 'sm' | 'md' | 'lg';
};

const SIZE_STYLES: Record<NonNullable<LoadingSpinnerProps['size']>, string> = {
  xs: 'h-3 w-3 border-[1.5px]',
  sm: 'h-4 w-4 border-2',
  md: 'h-5 w-5 border-2',
  lg: 'h-6 w-6 border-[2.5px]',
};

export function LoadingSpinner({ size = 'sm', className, ...props }: LoadingSpinnerProps) {
  return (
    <span
      role="status"
      aria-live="polite"
      className={cn(
        'inline-flex items-center justify-center rounded-full border-current/30 border-t-current animate-spin',
        SIZE_STYLES[size],
        className
      )}
      {...props}
    >
      <span className="sr-only">Loading</span>
    </span>
  );
}
