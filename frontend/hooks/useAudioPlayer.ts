"use client";

import { useCallback, useEffect, useRef, useState } from "react";

function waitForCanPlay(audio: HTMLAudioElement): Promise<void> {
  if (audio.readyState >= HTMLMediaElement.HAVE_FUTURE_DATA) {
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    const cleanup = () => {
      audio.removeEventListener("canplay", onReady);
      audio.removeEventListener("error", onError);
    };

    const onReady = () => {
      cleanup();
      resolve();
    };

    const onError = () => {
      cleanup();
      reject(new Error("Audio failed to load"));
    };

    audio.addEventListener("canplay", onReady);
    audio.addEventListener("error", onError);
  });
}

export function useAudioPlayer(url: string | null) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const audio = new Audio();
    audio.preload = "auto";
    audioRef.current = audio;

    const onEnded = () => setPlaying(false);
    const onPause = () => setPlaying(false);
    const onPlay = () => setPlaying(true);

    audio.addEventListener("ended", onEnded);
    audio.addEventListener("pause", onPause);
    audio.addEventListener("play", onPlay);

    return () => {
      audio.pause();
      audio.removeEventListener("ended", onEnded);
      audio.removeEventListener("pause", onPause);
      audio.removeEventListener("play", onPlay);
      audioRef.current = null;
    };
  }, []);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    let cancelled = false;

    const revokeObjectUrl = () => {
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };

    audio.pause();
    audio.currentTime = 0;
    setPlaying(false);
    setReady(false);
    revokeObjectUrl();

    if (!url) {
      audio.removeAttribute("src");
      return () => {
        cancelled = true;
        revokeObjectUrl();
      };
    }

    void (async () => {
      try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Audio request failed (${res.status})`);
        const blob = await res.blob();
        if (cancelled) return;

        const objectUrl = URL.createObjectURL(blob);
        objectUrlRef.current = objectUrl;
        audio.src = objectUrl;
        audio.load();
        await waitForCanPlay(audio);
        if (!cancelled) setReady(true);
      } catch {
        if (cancelled) return;
        audio.src = url;
        audio.load();
        try {
          await waitForCanPlay(audio);
          if (!cancelled) setReady(true);
        } catch {
          if (!cancelled) setReady(false);
        }
      }
    })();

    return () => {
      cancelled = true;
      revokeObjectUrl();
    };
  }, [url]);

  const play = useCallback(async () => {
    if (!url || !audioRef.current || !ready) return;
    try {
      await waitForCanPlay(audioRef.current);
      await audioRef.current.play();
    } catch {
      setPlaying(false);
    }
  }, [url, ready]);

  const pause = useCallback(() => {
    audioRef.current?.pause();
  }, []);

  const stop = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.pause();
    audio.currentTime = 0;
    setPlaying(false);
  }, []);

  return { play, pause, stop, playing, canPlay: !!url && ready };
}
