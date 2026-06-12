"use client";

import Link from "next/link";
import { Spinner } from "@/components/Spinner";
import type { EffectName, TransformParams } from "@/lib/types";
import { DEFAULT_EFFECTS } from "@/lib/effects";

export { DEFAULT_EFFECTS };

const EFFECTS: { label: string; value: EffectName }[] = [
  { label: "None", value: null },
  { label: "Robot", value: "robot" },
  { label: "Echo", value: "echo" },
  { label: "Reverb", value: "reverb" },
  { label: "Alien", value: "alien" },
];

interface EffectsAndSavePanelProps {
  params: TransformParams;
  onChange: (params: TransformParams) => void;
  presets: string[];
  onPreset: (name: string) => void;
  presetsDisabled?: boolean;
  profileName: string;
  onProfileNameChange: (name: string) => void;
  onSaveProfile: () => void;
  saveDisabled?: boolean;
  saveLoading?: boolean;
  processing?: boolean;
}

export function EffectsAndSavePanel({
  params,
  onChange,
  presets,
  onPreset,
  presetsDisabled,
  profileName,
  onProfileNameChange,
  onSaveProfile,
  saveDisabled,
  saveLoading,
  processing,
}: EffectsAndSavePanelProps) {
  return (
    <div className="panel panel-stack flex h-full flex-col">
      <div className="flex items-center justify-between gap-3">
        <h2 className="panel-title flex items-center gap-2">
          Voice Effects
          {processing && <Spinner className="h-3.5 w-3.5 text-ink-muted" />}
        </h2>
        <button
          type="button"
          className="btn text-xs"
          onClick={() => onChange(DEFAULT_EFFECTS)}
        >
          Default Effects
        </button>
      </div>

      <div className="panel-section">
        <div className="flex items-center justify-between text-xs">
          <span className="text-ink-muted">Pitch</span>
          <span className="font-mono font-semibold">
            {params.pitch_semitones >= 0 ? "+" : ""}
            {params.pitch_semitones.toFixed(1)} st
          </span>
        </div>
        <input
          type="range"
          min={-12}
          max={12}
          step={0.5}
          value={params.pitch_semitones}
          onChange={(e) =>
            onChange({ ...params, pitch_semitones: parseFloat(e.target.value) })
          }
          className="w-full accent-ink"
        />
      </div>

      <div className="panel-section">
        <div className="flex items-center justify-between text-xs">
          <span className="text-ink-muted">Speed</span>
          <span className="font-mono font-semibold">{params.speed_rate.toFixed(2)}×</span>
        </div>
        <input
          type="range"
          min={0.5}
          max={2}
          step={0.05}
          value={params.speed_rate}
          onChange={(e) =>
            onChange({ ...params, speed_rate: parseFloat(e.target.value) })
          }
          className="w-full accent-ink"
        />
      </div>

      <div>
        <label className="label">Effect</label>
        <select
          className="input"
          value={params.effect ?? "none"}
          onChange={(e) => {
            const v = e.target.value;
            onChange({
              ...params,
              effect: v === "none" ? null : (v as EffectName),
            });
          }}
        >
          {EFFECTS.map(({ label, value }) => (
            <option key={label} value={value ?? "none"}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <div className="min-h-0 flex-1">
        <p className="label">Presets</p>
        <div className="btn-row gap-2">
          {presets.map((name) => (
            <button
              key={name}
              type="button"
              className="btn px-2 py-1 text-[11px]"
              disabled={presetsDisabled}
              onClick={() => onPreset(name)}
            >
              {name}
            </button>
          ))}
        </div>
      </div>

      <div className="panel-divider panel-section">
        <h3 className="panel-title">Save as Profile</h3>
        <input
          className="input"
          value={profileName}
          onChange={(e) => onProfileNameChange(e.target.value)}
          placeholder="Profile name"
          disabled={saveDisabled}
        />
        <div className="btn-row">
          <button
            type="button"
            className="btn btn-primary flex flex-1 items-center justify-center gap-2 text-xs"
            disabled={saveDisabled || saveLoading}
            onClick={onSaveProfile}
          >
            {saveLoading ? (
              <>
                <Spinner className="h-3.5 w-3.5" />
                Saving…
              </>
            ) : (
              "Save Profile"
            )}
          </button>
          <Link href="/profiles" className="btn text-xs">
            Manage
          </Link>
        </div>
      </div>
    </div>
  );
}
