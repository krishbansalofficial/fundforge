"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { call, type ResultDetail } from "./account";

/** At the end of a run, ask the server to replay, verify and rank the room (once per desk). */
export function Ranked({ roomId, token }: { roomId: string; token: string | null }) {
  const [r, setR] = useState<ResultDetail | null>(null);
  const [error, setError] = useState("");
  const sent = useRef(false);
  useEffect(() => {
    if (!token || sent.current) return;
    sent.current = true;
    call<ResultDetail>(`/api/rooms/${roomId}/result`, { body: {}, seat: token }).then(setR).catch((e: Error) => setError(e.message));
  }, [roomId, token]);
  if (error) return <p className="muted">Not ranked: {error}</p>;
  if (!r) return <p role="status" className="muted">Verifying the run for the leaderboard…</p>;
  return (
    <p role="status">
      Verified and ranked with score {Number(r.score).toFixed(2)}. <Link href="/leaderboard">Leaderboard</Link> · <Link href={`/replay/${roomId}`}>Public replay</Link>
    </p>
  );
}
