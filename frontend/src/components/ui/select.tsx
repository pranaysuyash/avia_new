import React, { useState } from 'react';

export interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void; // Backward compatibility
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  placeholder?: string;
}

export const Select = React.forwardRef<HTMLDivElement, SelectProps>(
  ({ value, onValueChange, onChange, children, className = '', disabled, placeholder }, ref) => {
    const [isOpen, setIsOpen] = useState(false);
    const [selectedValue, setSelectedValue] = useState(value || '');

    const handleValueChange = (newValue: string) => {
      setSelectedValue(newValue);
      setIsOpen(false);
      onValueChange?.(newValue);
      // Trigger onChange for backward compatibility
      if (onChange) {
        const fakeEvent = {
          target: { value: newValue },
          currentTarget: { value: newValue }
        } as React.ChangeEvent<HTMLSelectElement>;
        onChange(fakeEvent);
      }
    };

    return (
      <div ref={ref} className={`relative ${className}`}>
        <SelectTrigger 
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          className={isOpen ? 'ring-2 ring-ring ring-offset-2' : ''}
        >
          <SelectValue>{selectedValue || placeholder || 'Select...'}</SelectValue>
        </SelectTrigger>
        {isOpen && (
          <SelectContent>
            {React.Children.map(children, (child) => {
              if (React.isValidElement(child) && child.type === SelectItem) {
                return React.cloneElement(child as React.ReactElement<SelectItemProps>, {
                  onClick: () => {
                    const itemValue = child.props.value || child.props.children;
                    if (typeof itemValue === 'string') {
                      handleValueChange(itemValue);
                    }
                  }
                });
              }
              return child;
            })}
          </SelectContent>
        )}
      </div>
    );
  }
);
Select.displayName = 'Select';

export const SelectTrigger = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ className = '', children, ...props }, ref) => (
    <button
      ref={ref}
      className={`flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      {...props}
    >
      {children}
      <span className="ml-2">▼</span>
    </button>
  )
);
SelectTrigger.displayName = 'SelectTrigger';

export const SelectValue = React.forwardRef<HTMLSpanElement, React.HTMLAttributes<HTMLSpanElement>>(
  ({ className = '', ...props }, ref) => (
    <span ref={ref} className={className} {...props} />
  )
);
SelectValue.displayName = 'SelectValue';

export const SelectContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', children, ...props }, ref) => (
    <div
      ref={ref}
      className={`absolute z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md ${className}`}
      {...props}
    >
      <div className="p-1">{children}</div>
    </div>
  )
);
SelectContent.displayName = 'SelectContent';

export interface SelectItemProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: string;
}

export const SelectItem = React.forwardRef<HTMLDivElement, SelectItemProps>(
  ({ className = '', children, value, ...props }, ref) => (
    <div
      ref={ref}
      className={`relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 ${className}`}
      data-value={value}
      {...props}
    >
      {children}
    </div>
  )
);
SelectItem.displayName = 'SelectItem';