"use client";

import { useEffect, useRef, useState } from "react";
import { call, setSession } from "../account";
import { Nav } from "../nav";

/** Email magic link: request a link, or (arriving from the email with #token=) spend it and keep the session. */
export default function Login() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sent" | "verifying">("idle");
  const [error, setError] = useState("");
  const spent = useRef(false);

  useEffect(() => {
    const token = new URLSearchParams(window.location.hash.replace(/^#/, "")).get("token");
    if (!token || spent.current) return;
    spent.current = true; // single use: never send it twice (React dev mode runs effects twice)
    window.history.replaceState(null, "", window.location.pathname);
    setState("verifying");
    call<{ session: string }>("/api/auth/verify", { body: { token } })
      .then((r) => { setSession(r.session); window.location.assign("/me"); })
      .catch((e: Error) => { setState("idle"); setError(e.message); });
  }, []);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await call("/api/auth/request", { body: { email } });
      setState("sent");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <main className="landing">
      <Nav />
      <h1>Sign in</h1>
      <p className="lede">Optional. Signing in keeps your game history and puts your name on the leaderboard. Guests can play without it.</p>
      {state === "verifying" ? <p role="status">Signing you in…</p>
        : state === "sent" ? <p role="status">Check your email for a sign-in link. It works once, for 15 minutes.</p>
        : (
          <form className="open-form" onSubmit={send}>
            <label>
              Email
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" maxLength={254} />
            </label>
            <button type="submit">Email me a link</button>
          </form>
        )}
      {error && <p className="error" role="alert">{error}</p>}
    </main>
  );
}
