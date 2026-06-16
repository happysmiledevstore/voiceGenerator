"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { UploadButton } from "@/components/AudioRecorder";
import { Spinner } from "@/components/Spinner";
import { useApiHealth } from "@/hooks/useApiHealth";
import {
  deleteSavedProfile,
  fetchSavedProfiles,
  profileExportUrl,
  saveProfile,
  updateSavedProfile,
  uploadAudio,
} from "@/lib/api";
import type { SavedVoiceProfile } from "@/lib/types";

function formatDate(iso: string) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function ProfilesPage() {
  const apiOnline = useApiHealth();
  const [status, setStatus] = useState("Manage your saved voice profiles.");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [importing, setImporting] = useState(false);
  const [addingSample, setAddingSample] = useState(false);
  const [profiles, setProfiles] = useState<SavedVoiceProfile[]>([]);
  const [selected, setSelected] = useState<SavedVoiceProfile | null>(null);
  const [editName, setEditName] = useState("");
  const [newName, setNewName] = useState("My Voice");
  const [pendingAudioId, setPendingAudioId] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const reload = useCallback(async (selectId?: string | null) => {
    const list = await fetchSavedProfiles();
    setProfiles(list);
    if (selectId === null) {
      setSelected(null);
    } else if (selectId) {
      setSelected(list.find((p) => p.id === selectId) ?? null);
    } else if (selected) {
      setSelected(list.find((p) => p.id === selected.id) ?? null);
    }
  }, [selected]);

  useEffect(() => {
    fetchSavedProfiles()
      .then(setProfiles)
      .catch(() => setProfiles([]));
  }, []);

  useEffect(() => {
    if (selected) setEditName(selected.name);
  }, [selected]);

  const handleUploadForProfile = async (file: File) => {
    setUploading(true);
    setStatus("Uploading audio for analysis...");
    try {
      const meta = await uploadAudio(file, file.name);
      setPendingAudioId(meta.id);
      setStatus(`Audio ready (${meta.duration_s.toFixed(1)}s). Click Create Profile.`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleCreateFromAudio = async () => {
    if (!pendingAudioId) {
      setStatus("Upload a voice recording first.");
      return;
    }
    setCreating(true);
    try {
      const saved = await saveProfile({
        name: newName.trim() || "My Voice",
        audio_id: pendingAudioId,
      });
      setSelected(saved);
      setEditName(saved.name);
      setPendingAudioId(null);
      await reload(saved.id);
      setStatus(`Profile created: ${saved.name}`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Create failed.");
    } finally {
      setCreating(false);
    }
  };

  const handleImport = async (file: File) => {
    setImporting(true);
    try {
      const data = JSON.parse(await file.text()) as SavedVoiceProfile;
      if (typeof data.pitch_mean !== "number") throw new Error("Invalid profile file.");
      const saved = await saveProfile({
        name: data.name || "Imported Voice",
        profile: {
          name: data.name || "Imported Voice",
          pitch_mean: data.pitch_mean,
          pitch_std: data.pitch_std ?? 0,
          speaking_rate: data.speaking_rate ?? 0,
          semitone_shift: data.semitone_shift,
          duration_s: data.duration_s ?? 0,
        },
      });
      setSelected(saved);
      await reload(saved.id);
      setStatus(`Imported: ${saved.name}`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Import failed.");
    } finally {
      setImporting(false);
    }
  };

  const handleRename = async () => {
    if (!selected || !editName.trim()) return;
    setBusy(true);
    try {
      const updated = await updateSavedProfile(selected.id, editName.trim());
      setSelected(updated);
      await reload(updated.id);
      setStatus(`Renamed to "${updated.name}".`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Rename failed.");
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!selected) return;
    if (!window.confirm(`Delete profile "${selected.name}"?`)) return;
    setBusy(true);
    try {
      await deleteSavedProfile(selected.id);
      setSelected(null);
      await reload(null);
      setStatus("Profile deleted.");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Delete failed.");
    } finally {
      setBusy(false);
    }
  };

  const handleExport = () => {
    if (!selected) return;
    const a = document.createElement("a");
    a.href = profileExportUrl(selected.id);
    a.download = "";
    a.click();
    setStatus(`Exported ${selected.name}.`);
  };

  const handleAddSample = async () => {
    if (!selected?.is_sample) return;
    setAddingSample(true);
    try {
      const saved = await saveProfile({
        name: selected.name,
        profile: {
          name: selected.name,
          pitch_mean: selected.pitch_mean,
          pitch_std: selected.pitch_std,
          speaking_rate: selected.speaking_rate,
          semitone_shift: selected.semitone_shift,
          duration_s: selected.duration_s,
        },
      });
      setSelected(saved);
      setEditName(saved.name);
      await reload(saved.id);
      setStatus(`Added "${saved.name}" to your profiles.`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Could not save sample.");
    } finally {
      setAddingSample(false);
    }
  };

  const sampleProfiles = profiles.filter((p) => p.is_sample);
  const savedProfiles = profiles.filter((p) => !p.is_sample);
  const pageBusy = busy || uploading || creating || importing || addingSample;

  return (
    <AppShell
      title="Voice Profiles"
      subtitle="Celebrity samples, your saved profiles, import & export"
      status={status}
      apiOnline={apiOnline}
      processing={pageBusy}
      titleVariant="hero"
    >
      <div className="mx-auto w-full max-w-2xl">
        <div className="panel panel-stack p-6 md:p-8">
          <div className="panel-section">
            <h2 className="panel-title">Celebrity Voice Samples</h2>
            <p className="text-[11px] leading-relaxed text-ink-muted">
              Stylized approximations based on typical pitch and pacing — for fun, not exact
              likenesses. Use on TTS or save to your profiles.
            </p>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {sampleProfiles.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  className={`rounded-lg border px-3 py-2.5 text-left text-sm transition ${selected?.id === p.id
                    ? "border-ink bg-surface-muted"
                    : "border-surface-border hover:bg-surface-muted"
                    }`}
                  onClick={() => setSelected(p)}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{p.name}</span>
                    <span className="rounded-full bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium text-amber-900">
                      Sample
                    </span>
                  </div>
                  {p.description && (
                    <p className="mt-1 line-clamp-2 text-[11px] text-ink-muted">{p.description}</p>
                  )}
                  <p className="mt-1 text-[10px] text-ink-muted">
                    {p.pitch_mean.toFixed(0)} Hz · {p.semitone_shift >= 0 ? "+" : ""}
                    {p.semitone_shift.toFixed(1)} st
                  </p>
                </button>
              ))}
            </div>
          </div>

          <div className="panel-divider panel-section">
            <h2 className="panel-title">Create Profile</h2>
            <input
              className="input"
              placeholder="Profile name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              disabled={pageBusy}
            />
            <div className="btn-row">
              <UploadButton
                disabled={pageBusy}
                loading={uploading}
                onFile={handleUploadForProfile}
              />
              <button
                type="button"
                className="btn btn-primary flex items-center gap-2 text-xs"
                disabled={pageBusy || !pendingAudioId}
                onClick={() => void handleCreateFromAudio()}
              >
                {creating ? (
                  <>
                    <Spinner className="h-3.5 w-3.5" />
                    Creating…
                  </>
                ) : (
                  "Create from Audio"
                )}
              </button>
              <button
                type="button"
                className="btn flex items-center gap-2 text-xs"
                disabled={pageBusy}
                onClick={() => fileRef.current?.click()}
              >
                {importing ? (
                  <>
                    <Spinner className="h-3.5 w-3.5" />
                    Importing…
                  </>
                ) : (
                  "Import JSON"
                )}
              </button>
            </div>
            {pendingAudioId && (
              <p className="text-[11px] text-ink-muted">Audio uploaded — ready to analyse.</p>
            )}
            <input
              ref={fileRef}
              type="file"
              accept=".json,.vgprofile,application/json"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void handleImport(f);
                e.target.value = "";
              }}
            />
          </div>

          <div className="panel-divider">
            <h2 className="panel-title mb-3">Your Profiles ({savedProfiles.length})</h2>
            <div className="max-h-48 space-y-2 overflow-y-auto">
              {savedProfiles.length === 0 ? (
                <p className="py-4 text-center text-xs text-ink-muted">
                  No personal profiles yet. Create one or add a celebrity sample.
                </p>
              ) : (
                savedProfiles.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${selected?.id === p.id
                      ? "border-ink bg-surface-muted"
                      : "border-surface-border hover:bg-surface-muted"
                      }`}
                    onClick={() => setSelected(p)}
                  >
                    <span className="font-medium">{p.name}</span>
                    <span className="ml-2 text-xs text-ink-muted">
                      {p.pitch_mean.toFixed(0)} Hz · {p.semitone_shift >= 0 ? "+" : ""}
                      {p.semitone_shift.toFixed(1)} st
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>

          {selected && (
            <div className="panel-divider panel-section">
              <div className="flex items-center justify-between gap-2">
                <h2 className="panel-title">Profile Details</h2>
                {selected.is_sample && (
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-900">
                    Celebrity sample
                  </span>
                )}
              </div>
              {selected.description && (
                <p className="text-xs text-ink-muted">{selected.description}</p>
              )}
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                <span className="text-ink-muted">Pitch mean</span>
                <span className="font-mono">{selected.pitch_mean.toFixed(1)} Hz</span>
                <span className="text-ink-muted">Pitch std</span>
                <span className="font-mono">{selected.pitch_std.toFixed(1)} Hz</span>
                <span className="text-ink-muted">Semitone shift</span>
                <span className="font-mono">
                  {selected.semitone_shift >= 0 ? "+" : ""}
                  {selected.semitone_shift.toFixed(1)} st
                </span>
                <span className="text-ink-muted">Speaking rate</span>
                <span className="font-mono">{selected.speaking_rate}</span>
                <span className="text-ink-muted">Sample duration</span>
                <span className="font-mono">{selected.duration_s.toFixed(1)}s</span>
                {!selected.is_sample && (
                  <>
                    <span className="text-ink-muted">Created</span>
                    <span>{formatDate(selected.created_at)}</span>
                    <span className="text-ink-muted">Updated</span>
                    <span>{formatDate(selected.updated_at)}</span>
                  </>
                )}
              </div>

              {selected.is_sample ? (
                <div className="btn-row">
                  <button
                    type="button"
                    className="btn btn-primary flex items-center gap-2 text-xs"
                    disabled={pageBusy}
                    onClick={() => void handleAddSample()}
                  >
                    {addingSample ? (
                      <>
                        <Spinner className="h-3.5 w-3.5" />
                        Saving…
                      </>
                    ) : (
                      "Add to My Profiles"
                    )}
                  </button>
                </div>
              ) : (
                <>
                  <div className="btn-row">
                    <input
                      className="input min-w-0 flex-1"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      disabled={busy}
                    />
                    <button
                      type="button"
                      className="btn btn-primary shrink-0 text-xs"
                      disabled={busy || !editName.trim()}
                      onClick={() => void handleRename()}
                    >
                      Rename
                    </button>
                  </div>

                  <div className="btn-row">
                    <button type="button" className="btn text-xs" onClick={handleExport}>
                      Export JSON
                    </button>
                    <button
                      type="button"
                      className="btn text-xs text-red-700"
                      disabled={busy}
                      onClick={() => void handleDelete()}
                    >
                      Delete
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
