import type { TransformParams } from "./types";

export const DEFAULT_EFFECTS: TransformParams = {
  pitch_semitones: 0,
  speed_rate: 1,
  effect: null,
};

export function isDefaultEffects(params: TransformParams): boolean {
  return (
    params.pitch_semitones === DEFAULT_EFFECTS.pitch_semitones &&
    params.speed_rate === DEFAULT_EFFECTS.speed_rate &&
    params.effect === DEFAULT_EFFECTS.effect
  );
}
