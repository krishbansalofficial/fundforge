"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getSession } from "./account";

/** Arena navigation: home, leaderboard, and sign in or profile. */
export function Nav() {
  const [signedIn, setSignedIn] = useState(false);
  useEffect(() => setSignedIn(Boolean(getSession())), []);
  return (
    <nav aria-label="Arena" className="tw:flex tw:flex-wrap tw:gap-4 tw:text-sm">
      <Link href="/">Play</Link>
      <Link href="/leaderboard">Leaderboard</Link>
      {signedIn ? <Link href="/me">Profile</Link> : <Link href="/login">Sign in</Link>}
    </nav>
  );
}
