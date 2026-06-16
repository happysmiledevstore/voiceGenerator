"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchSavedProfiles } from "@/lib/api";
import type { SavedVoiceProfile } from "@/lib/types";

interface ProfilePickerProps {
  selectedId: string | null;
  onSelect: (profile: SavedVoiceProfile | null) => void;
  disabled?: boolean;
  className?: string;
  embedded?: boolean;
}

export function ProfilePicker({
  selectedId,
  onSelect,
  disabled,
  className,
  embedded,
}: ProfilePickerProps) {
  const [profiles, setProfiles] = useState<SavedVoiceProfile[]>([]);

  useEffect(() => {
    fetchSavedProfiles()
      .then(setProfiles)
      .catch(() => setProfiles([]));
  }, []);

  const content = (
    <div className="panel-section">
      <div className="flex items-center justify-between gap-3">
        <h2 className="panel-title">Voice Profile</h2>
        <Link href="/profiles" className="text-[11px] text-accent hover:underline">
          Manage
        </Link>
      </div>
      <select
        className="input"
        value={selectedId ?? ""}
        disabled={disabled}
        onChange={(e) => {
          const id = e.target.value;
          if (!id) {
            onSelect(null);
            return;
          }
          const found = profiles.find((p) => p.id === id);
          onSelect(found ?? null);
        }}
      >
        <option value="">— None —</option>
        {profiles.map((p) => (
          <option key={p.id} value={p.id}>
            {p.is_sample ? "★ " : ""}
            {p.name} ({p.pitch_mean.toFixed(0)} Hz)
          </option>
        ))}
      </select>
      {profiles.length === 0 && (
        <p className="text-center text-[11px] text-ink-muted">
          No profiles yet.{" "}
          <Link href="/profiles" className="text-accent hover:underline">
            Create one
          </Link>
        </p>
      )}
    </div>
  );

  if (embedded) {
    return <div className={className ?? ""}>{content}</div>;
  }

  return (
    <div className={`panel ${className ?? ""}`}>
      {content}
    </div>
  );
}
