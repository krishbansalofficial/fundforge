"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { call, getSession, setSession, type Profile } from "../account";
import { Nav } from "../nav";

export default function Me() {
  const [p, setP] = useState<Profile | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getSession()) {
      window.location.assign("/login");
      return;
    }
    call<Profile>("/api/me").then((r) => { setP(r); setName(r.display_name); }).catch((e: Error) => setError(e.message));
  }, []);

  async function rename(e: React.FormEvent) {
    e.preventDefault();
    try {
      setP(await call<Profile>("/api/me", { method: "PATCH", body: { display_name: name } }));
      setError("");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function signOut() {
    await call("/api/auth/signout", { body: {} }).catch(() => undefined);
    setSession(null);
    window.location.assign("/");
  }

  return (
    <main className="landing">
      <Nav />
      <h1>Profile</h1>
      {error && <p className="error" role="alert">{error}</p>}
      {p && <>
        <form className="open-form" onSubmit={rename}>
          <label>
            Leaderboard name
            <input value={name} onChange={(e) => setName(e.target.value)} maxLength={24} />
          </label>
          <button type="submit">Save name</button>
        </form>
        <p className="muted">Signed in as {p.email}. <button type="button" className="link" onClick={signOut}>Sign out</button></p>
        <h2>Game history</h2>
        {p.games.length === 0 ? <p>No games yet. <Link href="/">Play one.</Link></p> : (
          <table>
            <thead><tr><th scope="col">Started</th><th scope="col">Scenario</th><th scope="col">Seat</th><th scope="col">Result</th><th scope="col" className="n">Score</th></tr></thead>
            <tbody>
              {p.games.map((g) => (
                <tr key={g.room_id}>
                  <td>{new Date(g.created_at).toLocaleString("en-US")}</td>
                  <td>{g.scenario}</td>
                  <td>{g.role === "pm" ? "Portfolio manager" : "Managing partner"}</td>
                  <td>{g.label ? <Link href={`/replay/${g.room_id}`}>{g.label}</Link> : "Unranked"}</td>
                  <td className="n">{g.score ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </>}
    </main>
  );
}
