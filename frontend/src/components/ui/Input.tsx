import React from 'react';
import { cn } from '../../lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', hasError = false, disabled, ...props }, ref) => {
    return (
      <input
        ref={ref}
        type={type}
        disabled={disabled}
        aria-invalid={hasError}
        className={cn(
          'w-full rounded-md border px-3 py-2 text-sm text-zinc-900 bg-white placeholder:text-zinc-400 transition-colors shadow-2xs',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1',
          hasError
            ? 'border-rose-300 focus-visible:ring-rose-500 text-rose-950 focus-visible:border-rose-500'
            : 'border-zinc-300 hover:border-zinc-400 focus-visible:ring-zinc-900 focus-visible:border-zinc-900',
          'disabled:opacity-50 disabled:bg-zinc-50 disabled:cursor-not-allowed',
          className
        )}
        {...props}
      />
    );
  }
);

Input.displayName = 'Input';
