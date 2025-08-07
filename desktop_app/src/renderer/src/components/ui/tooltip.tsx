import React from 'react';

interface TooltipContextType {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const TooltipContext = React.createContext<TooltipContextType | undefined>(undefined);

export interface TooltipProps {
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  delayDuration?: number;
  children?: React.ReactNode;
}

export const TooltipProvider: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

export const Tooltip: React.FC<TooltipProps> = ({ 
  open, 
  defaultOpen = false, 
  onOpenChange, 
  delayDuration = 700,
  children 
}) => {
  const [isOpen, setIsOpen] = React.useState(open ?? defaultOpen);

  React.useEffect(() => {
    if (open !== undefined) {
      setIsOpen(open);
    }
  }, [open]);

  const contextValue = React.useMemo(
    () => ({
      open: isOpen,
      onOpenChange: (newOpen: boolean) => {
        setIsOpen(newOpen);
        onOpenChange?.(newOpen);
      },
    }),
    [isOpen, onOpenChange]
  );

  return (
    <TooltipContext.Provider value={contextValue}>
      {children}
    </TooltipContext.Provider>
  );
};

export const TooltipTrigger = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ onMouseEnter, onMouseLeave, onFocus, onBlur, ...props }, ref) => {
    const context = React.useContext(TooltipContext);
    if (!context) throw new Error('TooltipTrigger must be used within Tooltip');

    return (
      <button
        ref={ref}
        onMouseEnter={(e) => {
          onMouseEnter?.(e);
          context.onOpenChange(true);
        }}
        onMouseLeave={(e) => {
          onMouseLeave?.(e);
          context.onOpenChange(false);
        }}
        onFocus={(e) => {
          onFocus?.(e);
          context.onOpenChange(true);
        }}
        onBlur={(e) => {
          onBlur?.(e);
          context.onOpenChange(false);
        }}
        {...props}
      />
    );
  }
);
TooltipTrigger.displayName = 'TooltipTrigger';

export const TooltipContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { side?: 'top' | 'right' | 'bottom' | 'left' }>(
  ({ className = '', side = 'top', ...props }, ref) => {
    const context = React.useContext(TooltipContext);
    if (!context) throw new Error('TooltipContent must be used within Tooltip');

    if (!context.open) return null;

    const sideStyles = {
      top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
      bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
      left: 'right-full top-1/2 -translate-y-1/2 mr-2',
      right: 'left-full top-1/2 -translate-y-1/2 ml-2',
    };

    return (
      <div
        ref={ref}
        className={`absolute z-50 overflow-hidden rounded-md border bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95 ${sideStyles[side]} ${className}`}
        {...props}
      />
    );
  }
);
TooltipContent.displayName = 'TooltipContent';