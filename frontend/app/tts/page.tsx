"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { EffectsPanel } from "@/components/EffectsPanel";
import { ProfilePicker } from "@/components/ProfilePicker";
import { Spinner } from "@/components/Spinner";
import { TransportBar } from "@/components/TransportBar";
import { Waveform } from "@/components/Waveform";
import { useAutoTransform } from "@/hooks/useAutoTransform";
import { useApiHealth } from "@/hooks/useApiHealth";
import {
  applyVoiceProfile,
  audioFileUrl,
  fetchOfflineVoices,
  fetchPresets,
  generateTTS,
} from "@/lib/api";
import { DEFAULT_EFFECTS } from "@/lib/effects";
import type { EffectName, OfflineVoice, PresetInfo, SavedVoiceProfile, TransformParams } from "@/lib/types";

const TTS_LANGUAGES = ["English", "Spanish", "French", "German", "Japanese"] as const;

export default function TTSPage() {
  const apiOnline = useApiHealth();
  const [status, setStatus] = useState("Enter text and generate speech.");
  const [processing, setProcessing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);
  const [text, setText] = useState("");
  const [engine, setEngine] = useState<"gtts" | "offline">("gtts");
  const [language, setLanguage] = useState<string>(TTS_LANGUAGES[0]);
  const [slow, setSlow] = useState(false);
  const [voices, setVoices] = useState<OfflineVoice[]>([]);
  const [voiceId, setVoiceId] = useState<string>("");
  const [presets, setPresets] = useState<string[]>([]);
  const [presetMap, setPresetMap] = useState<Record<string, PresetInfo>>({});
  const [effects, setEffects] = useState<TransformParams>(DEFAULT_EFFECTS);
  const [rawId, setRawId] = useState<string | null>(null);
  const [processedId, setProcessedId] = useState<string | null>(null);
  const [profileAudioId, setProfileAudioId] = useState<string | null>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<SavedVoiceProfile | null>(null);

  const rawUrl = rawId ? audioFileUrl(rawId) : null;
  const effectUrl = processedId ? audioFileUrl(processedId) : null;
  const profileUrl = profileAudioId ? audioFileUrl(profileAudioId) : null;
  const currentUrl = effectUrl ?? profileUrl ?? rawUrl;

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
    fetchOfflineVoices()
      .then(setVoices)
      .catch(() => { });
    fetchPresets()
      .then((list) => {
        setPresets(list.map((x) => x.name));
        setPresetMap(Object.fromEntries(list.map((x) => [x.name, x])));
      })
      .catch(() =>
        setPresets(["Normal", "Deep Voice", "Chipmunk", "Robot", "Echo", "Reverb", "Alien"]),
      );
  }, []);

  const handleGenerate = async () => {
    const trimmed = text.trim();
    if (!trimmed) {
      setStatus("Please enter some text.");
      return;
    }
    setGenerating(true);
    setStatus("Generating speech...");
    setProcessedId(null);
    setProfileAudioId(null);
    setEffects(DEFAULT_EFFECTS);
    try {
      const res = await generateTTS({
        text: trimmed,
        engine,
        language,
        slow,
        voice_id: voiceId || null,
      });
      setRawId(res.audio_id);
      setDuration(res.meta.duration_s);
      setStatus(`Generated ${res.meta.duration_s.toFixed(1)}s of speech.`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "TTS failed.");
    } finally {
      setGenerating(false);
    }
  };

  const handleApplyProfile = async () => {
    if (!rawId || !selectedProfile) return;
    setProfileLoading(true);
    setStatus("Applying voice profile...");
    try {
      const res = await applyVoiceProfile(rawId, { profileId: selectedProfile.id });
      setProfileAudioId(res.audio_id);
      setDuration(res.meta.duration_s);
      setStatus("Voice profile applied.");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Profile apply failed.");
    } finally {
      setProfileLoading(false);
    }
  };

  const busy = generating || profileLoading || processing;

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

  const handleDownload = () => {
    const id = processedId ?? profileAudioId ?? rawId;
    if (!id) return;
    const a = document.createElement("a");
    a.href = audioFileUrl(id);
    a.download = `speech_${id}.wav`;
    a.click();
  };

  return (
    <AppShell
      title="Text to Speech"
      subtitle="Generate speech and apply effects or a voice profile"
      status={status}
      apiOnline={apiOnline}
      processing={processing || busy}
      wide
      titleVariant="hero"
    >
      <div className="grid grid-cols-1 items-stretch gap-4 md:grid-cols-2">
        <div className="panel panel-stack flex h-full min-h-0 flex-col overflow-hidden">
          <div className="panel-section flex min-h-0 flex-1">
            <h2 className="panel-title shrink-0">Text</h2>
            <textarea
              className="input min-h-[8rem] flex-1 resize-none text-sm"
              placeholder="Type text to synthesise..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={busy}
            />
            <p className="shrink-0 text-center text-[11px] text-ink-muted">{text.length} characters</p>

            <div className="btn-row shrink-0 justify-center text-xs">
              <label className="flex items-center gap-1">
                <input
                  type="radio"
                  checked={engine === "gtts"}
                  onChange={() => setEngine("gtts")}
                  disabled={busy}
                />
                gTTS
              </label>
              <label className="flex items-center gap-1">
                <input
                  type="radio"
                  checked={engine === "offline"}
                  onChange={() => setEngine("offline")}
                  disabled={busy}
                />
                Offline
              </label>
            </div>

            {engine === "gtts" ? (
              <div className="btn-row shrink-0">
                <select
                  className="input flex-1"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  disabled={busy}
                >
                  {TTS_LANGUAGES.map((lang) => (
                    <option key={lang} value={lang}>
                      {lang}
                    </option>
                  ))}
                </select>
                <label className="flex shrink-0 items-center gap-1 text-xs">
                  <input
                    type="checkbox"
                    checked={slow}
                    onChange={(e) => setSlow(e.target.checked)}
                    disabled={busy}
                  />
                  Slow
                </label>
              </div>
            ) : (
              <select
                className="input shrink-0"
                value={voiceId}
                onChange={(e) => setVoiceId(e.target.value)}
                disabled={busy}
              >
                <option value="">Default voice</option>
                {voices.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
            )}

            <button
              type="button"
              className="btn btn-primary flex w-full shrink-0 items-center justify-center gap-2 py-2 text-sm font-semibold"
              disabled={busy}
              onClick={() => void handleGenerate()}
            >
              {generating ? (
                <>
                  <Spinner className="h-4 w-4" />
                  Generating…
                </>
              ) : (
                "Generate Speech"
              )}
            </button>
          </div>

          <div className="panel-divider shrink-0">
            <ProfilePicker
              selectedId={selectedProfile?.id ?? null}
              onSelect={setSelectedProfile}
              disabled={busy}
              embedded
            />
          </div>
        </div>

        <div className="panel panel-stack flex h-full min-h-0 flex-col overflow-hidden">
          <div className="panel-section shrink-0">
            <div className="flex shrink-0 items-center justify-between">
              <span className="text-xs text-ink-muted">Waveform</span>
              {duration != null && (
                <span className="text-xs text-ink-muted">{duration.toFixed(1)}s</span>
              )}
            </div>
            <Waveform
              url={currentUrl}
              color={processedId || profileAudioId ? "#18181b" : "#71717a"}
              height={88}
            />
            <TransportBar
              audioUrl={currentUrl}
              onDownload={handleDownload}
              onApplyProfile={handleApplyProfile}
              profileEnabled={!!selectedProfile && !!rawId}
              profileLoading={profileLoading}
              disabled={busy}
              applying={processing}
            />
          </div>

          <div className="panel-divider min-h-0 flex-1 overflow-auto">
            <EffectsPanel
              params={effects}
              onChange={setEffects}
              presets={presets}
              onPreset={handlePreset}
              presetsDisabled={!rawId || busy}
              processing={processing}
              embedded
              hideTitle
            />
          </div>
        </div>
      </div>
    </AppShell>
  );
}
