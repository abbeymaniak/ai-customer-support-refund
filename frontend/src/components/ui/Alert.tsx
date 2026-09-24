import React from 'react';
import { Info, CheckCircle2, AlertTriangle, AlertOctagon, X } from 'lucide-react';
import { cn } from '../../lib/utils';

export type AlertVariant = 'info' | 'success' | 'warning' | 'error';

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant;
  title?: string;
  onClose?: () => void;
}

const variantStyles: Record<AlertVariant, { container: string; icon: React.ReactNode }> = {
  info: {
    container: 'bg-zinc-50 border-zinc-200 text-zinc-900',
    icon: <Info className="h-5 w-5 text-zinc-600 shrink-0" aria-hidden="true" />,
  },
  success: {
    container: 'bg-emerald-50 border-emerald-200 text-emerald-950',
    icon: <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" aria-hidden="true" />,
  },
  warning: {
    container: 'bg-amber-50 border-amber-200 text-amber-950',
    icon: <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" aria-hidden="true" />,
  },
  error: {
    container: 'bg-rose-50 border-rose-200 text-rose-950',
    icon: <AlertOctagon className="h-5 w-5 text-rose-600 shrink-0" aria-hidden="true" />,
  },
};

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  onClose,
  className,
  children,
  ...props
}) => {
  const { container, icon } = variantStyles[variant];

  return (
    <div
      role="alert"
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border text-sm shadow-2xs',
        container,
        className
      )}
      {...props}
    >
      {icon}
      <div className="flex-1 flex flex-col gap-1">
        {title && <h5 className="font-semibold tracking-tight">{title}</h5>}
        <div className="text-zinc-600 text-xs leading-relaxed">{children}</div>
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="text-zinc-400 hover:text-zinc-600 p-0.5 rounded transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900"
          aria-label="Dismiss alert"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      )}
    </div>
  );
};
