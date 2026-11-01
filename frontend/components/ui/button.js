"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

const buttonVariants = (props) => {
  return cn(
    "inline-flex items-center justify-center rounded-medium text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
    "border border-input bg-background hover:bg-accent hover:text-accent-foreground text-primary-foreground",
    "h-10 px-4 py-2",
    props.className,
  );
};

export default function Button({ className, variant, ...props }) {
  return (
    <button
      type="button"
      className={cn(buttonVariants(), className)}
      {...props}
    />
  );
}
