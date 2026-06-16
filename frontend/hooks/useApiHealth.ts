"use client";

import { useEffect, useState } from "react";
import { checkHealth } from "@/lib/api";

const POLL_MS = 15_000;

export function useApiHealth() {
  const [apiOnline, setApiOnline] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      const ok = await checkHealth();
      if (!cancelled) setApiOnline(ok);
    };

    void poll();
    const id = setInterval(poll, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return apiOnline;
}
