import type {
  AudioMeta,
  OfflineVoice,
  PresetInfo,
  SavedVoiceProfile,
  TransformParams,
  TransformResponse,
  TTSResponse,
  VoiceProfile,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body.message ?? detail;
      if (Array.isArray(detail)) {
        detail = detail.map((d) => d.msg ?? String(d)).join(", ");
      }
    } catch {
      /* ignore */
    }
    throw new Error(String(detail));
  }
  return res.json() as Promise<T>;
}

export function audioFileUrl(audioId: string): string {
  return `${API_BASE}/api/audio/${audioId}/file`;
}

export async function uploadAudio(file: Blob, filename = "recording.webm"): Promise<AudioMeta> {
  const form = new FormData();
  form.append("file", file, filename);
  return request<AudioMeta>("/api/audio/upload", { method: "POST", body: form });
}

export async function transformAudio(
  audioId: string,
  params: TransformParams,
): Promise<TransformResponse> {
  return request<TransformResponse>("/api/audio/transform", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ audio_id: audioId, ...params }),
  });
}

export async function applyPreset(
  audioId: string,
  presetName: string,
): Promise<TransformResponse> {
  return request<TransformResponse>("/api/audio/apply-preset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ audio_id: audioId, preset_name: presetName }),
  });
}

export async function fetchPresets(): Promise<PresetInfo[]> {
  return request<PresetInfo[]>("/api/audio/presets");
}

export async function generateTTS(body: {
  text: string;
  engine: "gtts" | "offline";
  language: string;
  slow: boolean;
  voice_id?: string | null;
  rate?: number;
}): Promise<TTSResponse> {
  return request<TTSResponse>("/api/tts/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function fetchLanguages(): Promise<Record<string, string>> {
  return request<Record<string, string>>("/api/tts/languages");
}

export async function fetchOfflineVoices(): Promise<OfflineVoice[]> {
  return request<OfflineVoice[]>("/api/tts/voices");
}

export async function analyzeProfile(audioId: string): Promise<VoiceProfile> {
  return request<VoiceProfile>("/api/profiles/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ audio_id: audioId }),
  });
}

export async function fetchSavedProfiles(): Promise<SavedVoiceProfile[]> {
  return request<SavedVoiceProfile[]>("/api/profiles");
}

export async function saveProfile(body: {
  name: string;
  audio_id?: string;
  profile?: VoiceProfile;
}): Promise<SavedVoiceProfile> {
  return request<SavedVoiceProfile>("/api/profiles/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function deleteSavedProfile(profileId: string): Promise<void> {
  await request<{ deleted: string }>(`/api/profiles/${profileId}`, { method: "DELETE" });
}

export async function updateSavedProfile(
  profileId: string,
  name: string,
): Promise<SavedVoiceProfile> {
  return request<SavedVoiceProfile>(`/api/profiles/${profileId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export function profileExportUrl(profileId: string): string {
  return `${API_BASE}/api/profiles/${profileId}/export`;
}

export async function applyVoiceProfile(
  audioId: string,
  options: { profile?: VoiceProfile; profileId?: string },
): Promise<TransformResponse> {
  return request<TransformResponse>("/api/profiles/apply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      audio_id: audioId,
      profile: options.profile,
      profile_id: options.profileId,
    }),
  });
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
