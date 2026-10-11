/** Seat token from a seat link: `#t=` (never sent to servers or in Referer), or `?t=` from older links. */
export function seatTokenFromUrl(hash: string, search: string): string | null {
  return new URLSearchParams(hash.replace(/^#/, "")).get("t") ?? new URLSearchParams(search).get("t");
}
