import React from 'react';
import { cn } from '@/lib/utils';

interface PopoverProps {
  children: React.ReactNode;
  open: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function Popover({ children, open, onOpenChange }: PopoverProps) {
  return (
    <div className="relative">
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<any>, { open, onOpenChange });
        }
        return child;
      })}
    </div>
  );
}

interface PopoverTriggerProps {
  children: React.ReactNode;
  asChild?: boolean;
}

export function PopoverTrigger({ children }: PopoverTriggerProps) {
  return <>{children}</>;
}

interface PopoverContentProps {
  children: React.ReactNode;
  open?: boolean;
  align?: 'start' | 'center' | 'end';
  className?: string;
}

export function PopoverContent({ children, open, align = 'start', className }: PopoverContentProps) {
  if (!open) return null;

  return (
    <div
      className={cn(
        'absolute z-50 mt-2 w-full rounded-lg border border-white/10 bg-[hsl(var(--card))] p-2 shadow-lg',
        align === 'start' && 'left-0',
        align === 'center' && 'left-1/2 -translate-x-1/2',
        align === 'end' && 'right-0',
        className
      )}
    >
      {children}
    </div>
  );
}
