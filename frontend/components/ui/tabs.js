"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export function Tabs({ value, onValueChange, children, className }) {
  return (
    <div className={cn("space-y-4", className)}>
      {React.Children.map(children, (child) => {
        if (!React.isValidElement(child)) return child;
        return React.cloneElement(child, { activeValue: value, onValueChange });
      })}
    </div>
  );
}

export function TabsList({ activeValue, onValueChange, className, children }) {
  return (
    <div
      className={cn(
        "inline-flex h-10 items-center justify-start rounded-lg bg-muted p-1 text-muted-foreground",
        className
      )}
    >
      {React.Children.map(children, (child) => {
        if (!React.isValidElement(child)) return child;
        const isActive = child.props.value === activeValue;
        return React.cloneElement(child, {
          isActive,
          onClick: () => onValueChange && onValueChange(child.props.value),
        });
      })}
    </div>
  );
}

export function TabsTrigger({ value, isActive, onClick, className, children, ...props }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3.5 py-1.5 text-xs font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        isActive
          ? "bg-background text-foreground shadow-sm"
          : "hover:bg-background/50 hover:text-foreground",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function TabsContent({ value, activeValue, className, children, ...props }) {
  if (value !== activeValue) return null;
  return (
    <div
      className={cn("animate-in fade-in duration-150 focus-visible:outline-none", className)}
      {...props}
    >
      {children}
    </div>
  );
}
