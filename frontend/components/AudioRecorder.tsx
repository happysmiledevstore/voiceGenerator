"use client";

import { useEffect, useRef, useState } from "react";
import { Circle, Pause, Square, Upload } from "lucide-react";
import { Spinner } from "@/components/Spinner";
import { encodeWav, mergeFloat32Chunks, RECORD_SAMPLE_RATE } from "@/lib/wav";

function formatDuration(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const mins = Math.floor(s / 60);
  const secs = s % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

interface AudioRecorderProps {
  onRecorded: (blob: Blob) => void;
  disabled?: boolean;
  /** Shown when idle after a clip is loaded (not actively recording). */
  loadedDuration?: number | null;
  onRecordingDurationChange?: (seconds: number) => void;
}

export function AudioRecorder({
  onRecorded,
  disabled,
  loadedDuration,
  onRecordingDurationChange,
}: AudioRecorderProps) {
  const [recording, setRecording] = useState(false);
  const [paused, setPaused] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const streamRef = useRef<MediaStream | null>(null);
  const contextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const chunksRef = useRef<Float32Array[]>([]);
  const pausedRef = useRef(false);
  const tickStartRef = useRef<number | null>(null);
  const accumulatedRef = useRef(0);

  useEffect(() => {
    return () => {
      stopCapture(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!recording || paused) return;

    tickStartRef.current = performance.now();
    const id = window.setInterval(() => {
      const base = accumulatedRef.current;
      const running = tickStartRef.current
        ? (performance.now() - tickStartRef.current) / 1000
        : 0;
      const total = base + running;
      setElapsed(total);
      onRecordingDurationChange?.(total);
    }, 100);

    return () => window.clearInterval(id);
  }, [recording, paused, onRecordingDurationChange]);

  const resetTimer = () => {
    accumulatedRef.current = 0;
    tickStartRef.current = null;
    setElapsed(0);
    onRecordingDurationChange?.(0);
  };

  const stopCapture = (emit: boolean) => {
    processorRef.current?.disconnect();
    processorRef.current = null;

    if (contextRef.current) {
      void contextRef.current.close();
      contextRef.current = null;
    }

    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;

    if (emit && chunksRef.current.length > 0) {
      const merged = mergeFloat32Chunks(chunksRef.current);
      const wav = encodeWav(merged, RECORD_SAMPLE_RATE);
      if (wav.size > 0) onRecorded(wav);
    }

    chunksRef.current = [];
    setRecording(false);
    setPaused(false);
    pausedRef.current = false;
  };

  const start = async () => {
    try {
      resetTimer();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const context = new AudioContext({ sampleRate: RECORD_SAMPLE_RATE });
      await context.resume();

      const source = context.createMediaStreamSource(stream);
      const processor = context.createScriptProcessor(4096, 1, 1);

      chunksRef.current = [];
      pausedRef.current = false;

      processor.onaudioprocess = (event) => {
        if (pausedRef.current) return;
        const channel = event.inputBuffer.getChannelData(0);
        chunksRef.current.push(new Float32Array(channel));
      };

      source.connect(processor);
      processor.connect(context.destination);

      streamRef.current = stream;
      contextRef.current = context;
      processorRef.current = processor;
      setRecording(true);
      setPaused(false);
    } catch {
      alert("Microphone access denied or unavailable.");
    }
  };

  const pause = () => {
    if (!recording) return;
    if (!pausedRef.current && tickStartRef.current) {
      accumulatedRef.current += (performance.now() - tickStartRef.current) / 1000;
      tickStartRef.current = null;
    }
    pausedRef.current = !pausedRef.current;
    setPaused(pausedRef.current);
    if (!pausedRef.current) {
      tickStartRef.current = performance.now();
    }
  };

  const stop = () => {
    if (!recording) return;
    if (tickStartRef.current) {
      accumulatedRef.current += (performance.now() - tickStartRef.current) / 1000;
    }
    setElapsed(accumulatedRef.current);
    onRecordingDurationChange?.(accumulatedRef.current);
    stopCapture(true);
  };

  const displaySeconds =
    recording || paused ? elapsed : loadedDuration != null ? loadedDuration : 0;

  return (
    <div className="panel-section">
      <p className="font-mono text-lg font-semibold tabular-nums text-ink">
        {formatDuration(displaySeconds)}
        {(recording || paused) && (
          <span className="ml-2 text-xs font-normal text-red-600">
            {paused ? "Paused" : "Recording"}
          </span>
        )}
      </p>
      <div className="btn-row">
        <button
          type="button"
          className="btn btn-icon"
          onClick={start}
          disabled={disabled || recording}
          title="Record"
        >
          <Circle className={`h-5 w-5 ${recording ? "text-red-500 fill-red-500" : ""}`} />
        </button>
        <button
          type="button"
          className="btn btn-icon"
          onClick={pause}
          disabled={!recording}
          title={paused ? "Resume" : "Pause"}
        >
          <Pause className="h-5 w-5" />
        </button>
        <button
          type="button"
          className="btn btn-icon"
          onClick={stop}
          disabled={!recording}
          title="Stop"
        >
          <Square className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}

interface UploadButtonProps {
  onFile: (file: File) => void;
  disabled?: boolean;
  loading?: boolean;
}

export function UploadButton({ onFile, disabled, loading }: UploadButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="audio/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFile(file);
          e.target.value = "";
        }}
      />
      <button
        type="button"
        className="btn btn-icon"
        disabled={disabled || loading}
        title="Upload audio"
        onClick={() => inputRef.current?.click()}
      >
        {loading ? <Spinner className="h-5 w-5" /> : <Upload className="h-5 w-5" />}
      </button>
    </>
  );
}
