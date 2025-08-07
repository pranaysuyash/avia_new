import React from 'react';

export interface ToastProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'destructive';
  onClose?: () => void;
}

const toastVariants = {
  default: 'border bg-background text-foreground',
  destructive: 'destructive group border-destructive bg-destructive text-destructive-foreground',
};

export const Toast = React.forwardRef<HTMLDivElement, ToastProps>(
  ({ className = '', variant = 'default', onClose, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-6 pr-8 shadow-lg transition-all ${toastVariants[variant]} ${className}`}
        {...props}
      >
        <div className="grid gap-1">{children}</div>
        {onClose && (
          <button
            onClick={onClose}
            className="absolute right-2 top-2 rounded-md p-1 text-foreground/50 opacity-0 transition-opacity hover:text-foreground focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100"
          >
            ×
          </button>
        )}
      </div>
    );
  }
);
Toast.displayName = 'Toast';

export const ToastTitle = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`text-sm font-semibold ${className}`}
      {...props}
    />
  )
);
ToastTitle.displayName = 'ToastTitle';

export const ToastDescription = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`text-sm opacity-90 ${className}`}
      {...props}
    />
  )
);
ToastDescription.displayName = 'ToastDescription';