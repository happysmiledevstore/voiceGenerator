"use client";

import { useEffect, useRef } from "react";

interface WaveformProps {
  url?: string | null;
  color?: string;
  height?: number;
}

export function Waveform({ url, color = "#52525b", height = 72 }: WaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const drawEmpty = () => {
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "#fafafa";
      ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = "#e4e4e7";
      ctx.beginPath();
      ctx.moveTo(0, h / 2);
      ctx.lineTo(w, h / 2);
      ctx.stroke();
    };

    if (!url) {
      drawEmpty();
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const res = await fetch(url);
        const buf = await res.arrayBuffer();
        const audioCtx = new AudioContext();
        const decoded = await audioCtx.decodeAudioData(buf.slice(0));
        await audioCtx.close();

        if (cancelled) return;

        const data = decoded.getChannelData(0);
        const w = canvas.width;
        const h = canvas.height;
        const step = Math.ceil(data.length / w);

        ctx.clearRect(0, 0, w, h);
        ctx.fillStyle = "#fafafa";
        ctx.fillRect(0, 0, w, h);

        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.beginPath();

        for (let x = 0; x < w; x++) {
          const start = x * step;
          let min = 1;
          let max = -1;
          for (let i = 0; i < step && start + i < data.length; i++) {
            const v = data[start + i];
            if (v < min) min = v;
            if (v > max) max = v;
          }
          const yMin = ((1 - min) / 2) * h;
          const yMax = ((1 - max) / 2) * h;
          ctx.moveTo(x, yMin);
          ctx.lineTo(x, yMax);
        }
        ctx.stroke();
      } catch {
        if (!cancelled) drawEmpty();
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [url, color]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const resize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      canvas.width = parent.clientWidth;
      canvas.height = height;
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [height]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full rounded-lg border border-surface-border"
      style={{ height }}
    />
  );
}
