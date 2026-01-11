import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { ControlsToggle } from './ControlsToggle';

type AvoidRect = {
  left: number;
  right: number;
  top: number;
  bottom: number;
};

interface TheaterShellProps {
  controls: ReactNode;
  overlayLegend?: ReactNode;
  controlsOpen: boolean;
  onControlsToggle: () => void;
  onExit: () => void;
  children: (tooltipAvoidRect: AvoidRect | null) => ReactNode;
}

export function TheaterShell({
  controls,
  overlayLegend,
  controlsOpen,
  onControlsToggle,
  onExit,
  children,
}: TheaterShellProps) {
  const viewControlsRef = useRef<HTMLDivElement | null>(null);
  const [tooltipAvoidRect, setTooltipAvoidRect] = useState<AvoidRect | null>(
    null
  );

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onExit();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onExit]);

  const updateTooltipAvoidRect = useCallback(() => {
    if (!viewControlsRef.current || !controlsOpen) {
      setTooltipAvoidRect(null);
      return;
    }
    const rect = viewControlsRef.current.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) {
      setTooltipAvoidRect(null);
      return;
    }
    setTooltipAvoidRect({
      left: rect.left,
      right: rect.right,
      top: rect.top,
      bottom: rect.bottom,
    });
  }, [controlsOpen]);

  useLayoutEffect(() => {
    if (!controlsOpen) {
      setTooltipAvoidRect(null);
      return;
    }
    updateTooltipAvoidRect();
    const element = viewControlsRef.current;
    if (!element) {
      return;
    }
    const observer = new ResizeObserver(() => updateTooltipAvoidRect());
    observer.observe(element);
    window.addEventListener('resize', updateTooltipAvoidRect);
    return () => {
      observer.disconnect();
      window.removeEventListener('resize', updateTooltipAvoidRect);
    };
  }, [controlsOpen, updateTooltipAvoidRect]);

  return (
    <div className="fixed inset-0 z-50 bg-slate-950">
      <section className="absolute inset-0 overflow-hidden bg-gradient-to-br from-slate-900/70 via-slate-950/80 to-slate-950/95">
        {overlayLegend}
        {children(tooltipAvoidRect)}
      </section>
      <div className="absolute right-6 top-6 z-30 sm:hidden">
        <ControlsToggle controlsOpen={controlsOpen} onToggle={onControlsToggle} />
      </div>
      <aside
        ref={viewControlsRef}
        className={`absolute left-6 top-6 z-20 w-80 max-w-[calc(100%-3rem)] ${
          controlsOpen ? 'block' : 'hidden'
        } sm:block`}
      >
        {controls}
      </aside>
    </div>
  );
}
