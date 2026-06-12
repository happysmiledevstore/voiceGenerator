export type EffectName = "robot" | "echo" | "reverb" | "alien" | null;

export interface AudioMeta {
  id: string;
  sample_rate: number;
  duration_s: number;
  source: string;
  created_at: string;
}

export interface TransformParams {
  pitch_semitones: number;
  speed_rate: number;
  effect: EffectName;
}

export interface PresetInfo {
  name: string;
  pitch: number;
  speed: number;
  effect: string | null;
}

export interface VoiceProfile {
  name: string;
  pitch_mean: number;
  pitch_std: number;
  speaking_rate: number;
  semitone_shift: number;
  duration_s: number;
}

export interface SavedVoiceProfile extends VoiceProfile {
  id: string;
  created_at: string;
  updated_at: string;
}

export interface OfflineVoice {
  id: string;
  name: string;
  lang: string;
}

export interface TransformResponse {
  audio_id: string;
  meta: AudioMeta;
}

export interface TTSResponse {
  audio_id: string;
  meta: AudioMeta;
}
