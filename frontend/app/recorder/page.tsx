"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { AudioRecorder, UploadButton } from "@/components/AudioRecorder";
import { EffectsAndSavePanel } from "@/components/EffectsAndSavePanel";
import { TransportBar } from "@/components/TransportBar";
import { Waveform } from "@/components/Waveform";
import { useAutoTransform } from "@/hooks/useAutoTransform";
import {
  audioFileUrl,
  checkHealth,
  fetchPresets,
  saveProfile,
  uploadAudio,
} from "@/lib/api";
import { DEFAULT_EFFECTS } from "@/lib/effects";
import type { EffectName, PresetInfo, TransformParams } from "@/lib/types";

export default function RecorderPage() {
  const [apiOnline, setApiOnline] = useState(false);
  const [status, setStatus] = useState("Record or upload audio to get started.");
  const [processing, setProcessing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [presets, setPresets] = useState<string[]>([]);
  const [presetMap, setPresetMap] = useState<Record<string, PresetInfo>>({});
  const [effects, setEffects] = useState<TransformParams>(DEFAULT_EFFECTS);
  const [rawId, setRawId] = useState<string | null>(null);
  const [processedId, setProcessedId] = useState<string | null>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [profileName, setProfileName] = useState("My Voice");

  const rawUrl = rawId ? audioFileUrl(rawId) : null;
  const processedUrl = processedId ? audioFileUrl(processedId) : null;
  const currentUrl = processedUrl ?? rawUrl;

  const handleProcessed = useCallback((id: string | null, dur: number | null) => {
    setProcessedId(id);
    if (dur != null) setDuration(dur);
  }, []);

  useAutoTransform({
    rawId,
    effects,
    onResult: handleProcessed,
    onProcessing: setProcessing,
    onError: setStatus,
  });

  useEffect(() => {
    checkHealth().then(setApiOnline);
    fetchPresets()
      .then((list) => {
        setPresets(list.map((x) => x.name));
        setPresetMap(Object.fromEntries(list.map((x) => [x.name, x])));
      })
      .catch(() =>
        setPresets(["Normal", "Deep Voice", "Chipmunk", "Robot", "Echo", "Reverb", "Alien"]),
      );
  }, []);

  const ingest = useCallback(async (file: Blob, filename: string) => {
    setUploading(true);
    setStatus("Uploading...");
    setEffects(DEFAULT_EFFECTS);
    setProcessedId(null);
    try {
      const meta = await uploadAudio(file, filename);
      setRawId(meta.id);
      setDuration(meta.duration_s);
      setStatus(`Loaded ${meta.duration_s.toFixed(1)}s of audio.`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }, []);

  const handlePreset = (name: string) => {
    const preset = presetMap[name];
    if (!preset) return;
    setEffects({
      pitch_semitones: preset.pitch,
      speed_rate: preset.speed,
      effect: preset.effect as EffectName,
    });
    setStatus(`Preset "${name}" selected.`);
  };

  const handleSaveProfile = async () => {
    if (!rawId) return;
    setSavingProfile(true);
    try {
      const saved = await saveProfile({ name: profileName.trim() || "My Voice", audio_id: rawId });
      setStatus(`Profile saved: ${saved.name}`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Save profile failed.");
    } finally {
      setSavingProfile(false);
    }
  };

  const busy = uploading || savingProfile || processing;

  const handleDownload = () => {
    const id = processedId ?? rawId;
    if (!id) return;
    const a = document.createElement("a");
    a.href = audioFileUrl(id);
    a.download = `${id}.wav`;
    a.click();
  };

  return (
    <AppShell
      title="Voice Recorder"
      subtitle="Record, apply effects, and save audio"
      status={status}
      apiOnline={apiOnline}
      processing={processing || busy}
      wide
      titleVariant="hero"
    >
      <div className="grid grid-cols-1 items-stretch gap-4 md:grid-cols-2">
        <div className="flex h-full flex-col gap-4">
          <div className="panel panel-stack shrink-0">
            <div className="flex items-center justify-between gap-3">
              <h2 className="panel-title">Record</h2>
              <UploadButton
                disabled={busy || !apiOnline}
                loading={uploading}
                onFile={(file) => ingest(file, file.name)}
              />
            </div>
            <AudioRecorder
              disabled={busy || !apiOnline}
              loadedDuration={duration}
              onRecorded={(blob) => ingest(blob, "recording.wav")}
            />
          </div>

          <div className="panel panel-stack flex min-h-0 flex-1 flex-col">
            <div className="flex items-center justify-between">
              <span className="text-xs text-ink-muted">Waveform</span>
              {duration != null && (
                <span className="text-xs text-ink-muted">{duration.toFixed(1)}s</span>
              )}
            </div>
            <div className="flex min-h-0 flex-1 flex-col justify-center">
              <Waveform url={currentUrl} color={processedId ? "#18181b" : "#71717a"} height={88} />
            </div>
            <TransportBar
              audioUrl={currentUrl}
              onDownload={handleDownload}
              disabled={busy || !apiOnline}
              applying={processing}
            />
          </div>
        </div>

        <EffectsAndSavePanel
          params={effects}
          onChange={setEffects}
          presets={presets}
          onPreset={handlePreset}
          presetsDisabled={!rawId || busy}
          profileName={profileName}
          onProfileNameChange={setProfileName}
          onSaveProfile={() => void handleSaveProfile()}
          saveDisabled={busy || !rawId}
          saveLoading={savingProfile}
          processing={processing}
        />
      </div>
    </AppShell>
  );
}
