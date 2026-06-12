"use client";

import type { ReactNode } from "react";
import { StatusBar } from "@/components/StatusBar";

interface AppShellProps {
  title: string;
  subtitle?: string;
  status: string;
  apiOnline: boolean;
  processing?: boolean;
  wide?: boolean;
  titleVariant?: "default" | "hero";
  children: ReactNode;
}

/** Center-focused workspace — content capped and horizontally centered. */
export function AppShell({
  title,
  subtitle,
  status,
  apiOnline,
  processing,
  wide,
  titleVariant = "default",
  children,
}: AppShellProps) {
  const hero = titleVariant === "hero";

  return (
    <div className="flex h-full flex-col">
      <StatusBar message={status} apiOnline={apiOnline} processing={processing} />
      <div className="flex min-h-0 flex-1 items-center justify-center overflow-auto p-4">
        <div
          className={`flex w-full flex-col ${hero ? "gap-10" : "gap-3"} ${wide ? "max-w-5xl" : "max-w-3xl"}`}
        >
          <header className="shrink-0 text-center">
            <h1
              className={
                hero
                  ? "text-4xl font-bold tracking-tight text-ink md:text-5xl"
                  : "text-base font-bold text-ink"
              }
            >
              {title}
            </h1>
            {subtitle && (
              <p className={`text-ink-muted ${hero ? "mt-2 text-sm" : "mt-0.5 text-xs"}`}>
                {subtitle}
              </p>
            )}
          </header>
          {children}
        </div>
      </div>
    </div>
  );
}
