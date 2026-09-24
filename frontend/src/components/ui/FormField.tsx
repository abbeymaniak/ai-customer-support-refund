import React from 'react';
import { cn } from '../../lib/utils';

export interface FormFieldProps {
  id: string;
  label: string;
  helperText?: string;
  error?: string;
  required?: boolean;
  className?: string;
  children: React.ReactNode;
}

export const FormField: React.FC<FormFieldProps> = ({
  id,
  label,
  helperText,
  error,
  required = false,
  className,
  children,
}) => {
  const helperId = helperText ? `${id}-helper` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [errorId, helperId].filter(Boolean).join(' ') || undefined;

  // Clone child input to inject id, aria-describedby, and aria-invalid automatically if it's a valid React element
  const enhancedChild = React.isValidElement(children)
    ? React.cloneElement(
        children as React.ReactElement<{
          id?: string;
          'aria-describedby'?: string;
          hasError?: boolean;
        }>,
        {
          id,
          'aria-describedby': describedBy,
          hasError: Boolean(error),
        }
      )
    : children;

  return (
    <div className={cn('flex flex-col gap-1.5 text-left', className)}>
      <label
        htmlFor={id}
        className="text-xs font-semibold uppercase tracking-wider text-zinc-700 select-none"
      >
        {label}
        {required && (
          <span className="text-rose-600 ml-1" aria-hidden="true">
            *
          </span>
        )}
      </label>
      {enhancedChild}
      {error && (
        <p id={errorId} className="text-xs font-medium text-rose-600 mt-0.5" role="alert">
          {error}
        </p>
      )}
      {!error && helperText && (
        <p id={helperId} className="text-xs text-zinc-500 mt-0.5">
          {helperText}
        </p>
      )}
    </div>
  );
};
