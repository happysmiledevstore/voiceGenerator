"use client";

import { Download, Pause, Play, Square } from "lucide-react";
import { Spinner } from "@/components/Spinner";
import { useAudioPlayer } from "@/hooks/useAudioPlayer";

interface TransportBarProps {
  audioUrl: string | null;
  onDownload: () => void;
  onApplyProfile?: () => void;
  profileEnabled?: boolean;
  profileLoading?: boolean;
  applying?: boolean;
  disabled?: boolean;
}

export function TransportBar({
  audioUrl,
  onDownload,
  onApplyProfile,
  profileEnabled,
  profileLoading,
  applying,
  disabled,
}: TransportBarProps) {
  const { play, pause, stop, playing, canPlay } = useAudioPlayer(audioUrl);
  const blocked = disabled || applying || profileLoading;

  return (
    <div className="btn-row">
      <button
        type="button"
        className="btn btn-icon"
        disabled={!canPlay || blocked}
        title="Play"
        onClick={() => void play()}
      >
        <Play className="h-5 w-5" />
      </button>
      <button
        type="button"
        className="btn btn-icon"
        disabled={!canPlay || !playing || blocked}
        title="Pause"
        onClick={pause}
      >
        <Pause className="h-5 w-5" />
      </button>
      <button
        type="button"
        className="btn btn-icon"
        disabled={!canPlay || blocked}
        title="Stop"
        onClick={stop}
      >
        <Square className="h-5 w-5" />
      </button>

      <div className="mx-1 h-6 w-px bg-surface-border" />

      <button
        type="button"
        className="btn btn-icon"
        disabled={!canPlay || blocked}
        title="Download"
        onClick={onDownload}
      >
        <Download className="h-5 w-5" />
      </button>

      {onApplyProfile && (
        <button
          type="button"
          className="btn flex items-center gap-2 px-3 text-xs font-semibold"
          disabled={!profileEnabled || blocked}
          title="Apply voice profile"
          onClick={onApplyProfile}
        >
          {profileLoading ? (
            <>
              <Spinner className="h-3.5 w-3.5" />
              Processing…
            </>
          ) : (
            "Apply Profile"
          )}
        </button>
      )}
    </div>
  );
}
