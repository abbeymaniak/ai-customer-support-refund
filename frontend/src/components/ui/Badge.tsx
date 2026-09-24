import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Clock, Eye, ShieldAlert } from 'lucide-react';
import { cn } from '../../lib/utils';

export type BadgeStatus =
  'approved' | 'denied' | 'escalated' | 'pending' | 'manual_review' | 'neutral';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status?: BadgeStatus;
  size?: 'sm' | 'md';
  showIcon?: boolean;
  icon?: React.ReactNode;
}

const statusStyles: Record<BadgeStatus, string> = {
  approved: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  denied: 'bg-rose-50 text-rose-800 border-rose-200',
  escalated: 'bg-amber-50 text-amber-800 border-amber-200',
  pending: 'bg-zinc-100 text-zinc-800 border-zinc-300',
  manual_review: 'bg-violet-50 text-violet-800 border-violet-200',
  neutral: 'bg-zinc-50 text-zinc-700 border-zinc-200',
};

const defaultIcons: Record<BadgeStatus, React.ReactNode> = {
  approved: <CheckCircle2 className="h-3 w-3 text-emerald-600" aria-hidden="true" />,
  denied: <XCircle className="h-3 w-3 text-rose-600" aria-hidden="true" />,
  escalated: <AlertTriangle className="h-3 w-3 text-amber-600" aria-hidden="true" />,
  pending: <Clock className="h-3 w-3 text-zinc-600" aria-hidden="true" />,
  manual_review: <Eye className="h-3 w-3 text-violet-600" aria-hidden="true" />,
  neutral: <ShieldAlert className="h-3 w-3 text-zinc-500" aria-hidden="true" />,
};

export const Badge: React.FC<BadgeProps> = ({
  status = 'neutral',
  size = 'md',
  showIcon = true,
  icon,
  className,
  children,
  ...props
}) => {
  const displayIcon = icon ?? (showIcon ? defaultIcons[status] : null);

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-medium border rounded-full select-none capitalize',
        size === 'sm' ? 'px-2 py-0.5 text-2xs' : 'px-2.5 py-0.5 text-xs',
        statusStyles[status],
        className
      )}
      {...props}
    >
      {displayIcon && <span className="inline-flex shrink-0">{displayIcon}</span>}
      <span>{children ?? status.replace('_', ' ')}</span>
    </span>
  );
};
