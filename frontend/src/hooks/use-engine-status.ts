import { useEffect, useState } from "react";
import { api } from "@/api/client";
import type { EngineStatus } from "@/types/graph";

export function useEngineStatus(pollMs = 10_000) {
  const [status, setStatus] = useState<EngineStatus | null>(null);

  useEffect(() => {
    let active = true;
    const poll = async () => {
      try {
        const s = await api.getStatus();
        if (active) setStatus(s);
      } catch {
        if (active) setStatus(null);
      }
    };
    poll();
    const id = setInterval(poll, pollMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [pollMs]);

  return status;
}
