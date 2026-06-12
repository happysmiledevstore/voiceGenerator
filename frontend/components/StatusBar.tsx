"use client";

interface StatusBarProps {
  message: string;
  apiOnline: boolean;
  processing?: boolean;
}

export function StatusBar({ message, apiOnline, processing }: StatusBarProps) {
  return (
    <div className="flex shrink-0 items-center justify-between gap-3 border-b border-surface-border bg-surface px-4 py-2 text-xs">
      <span className="truncate text-ink-muted">{message}</span>
      <div className="flex shrink-0 items-center gap-2">
        {processing && (
          <span className="rounded-full bg-amber-100 px-2 py-0.5 font-medium text-amber-800">
            Processing…
          </span>
        )}
        <span
          className={`rounded-full px-2 py-0.5 font-medium ${apiOnline ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"
            }`}
        >
          API {apiOnline ? "online" : "offline"}
        </span>
      </div>
    </div>
  );
}
