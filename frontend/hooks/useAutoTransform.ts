"use client";

import { useEffect, useRef } from "react";
import { transformAudio } from "@/lib/api";
import { isDefaultEffects } from "@/lib/effects";
import type { TransformParams } from "@/lib/types";

interface Options {
  rawId: string | null;
  effects: TransformParams;
  onResult: (processedId: string | null, duration: number | null) => void;
  onProcessing?: (processing: boolean) => void;
  onError?: (message: string) => void;
}

export function useAutoTransform({
  rawId,
  effects,
  onResult,
  onProcessing,
  onError,
}: Options) {
  const requestRef = useRef(0);

  useEffect(() => {
    if (!rawId) {
      onResult(null, null);
      return;
    }

    if (isDefaultEffects(effects)) {
      onResult(null, null);
      return;
    }

    const requestId = ++requestRef.current;
    onProcessing?.(true);

    const timer = window.setTimeout(async () => {
      try {
        const res = await transformAudio(rawId, effects);
        if (requestRef.current !== requestId) return;
        onResult(res.audio_id, res.meta.duration_s);
      } catch (e) {
        if (requestRef.current !== requestId) return;
        onError?.(e instanceof Error ? e.message : "Effect update failed.");
      } finally {
        if (requestRef.current === requestId) onProcessing?.(false);
      }
    }, 350);

    return () => window.clearTimeout(timer);
  }, [rawId, effects, onResult, onProcessing, onError]);
}
