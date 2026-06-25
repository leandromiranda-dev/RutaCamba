import * as React from "react";
import { cn } from "@/lib/utils";

type Variant = "default" | "secondary" | "outline" | "success" | "destructive";

const variants: Record<Variant, string> = {
  default: "bg-primary/15 text-primary border-primary/30",
  secondary: "bg-secondary text-secondary-foreground border-border",
  outline: "border-border text-foreground",
  success: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  destructive: "bg-destructive/15 text-red-300 border-destructive/30",
};

export function Badge({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: Variant }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
