import type { components } from "./api-types";

type LedgerPage = components["schemas"]["LedgerPage"];
type JournalEntry = components["schemas"]["JournalEntry"];

/** The server's page size for `GET /api/rooms/{id}/ledger`. */
export const LEDGER_PAGE = 1000;

/** A contiguous run of one entity's journal: `entries[i]` is entry number `start + i`.
 *  The journal is append-only, so an entry's number (the cursor), not its array slot, identifies it. */
export type Journal = { start: number; next: number; entries: JournalEntry[]; digest: string };

/** Fold one ledger page (entries `next - entries.length` up to `next`) into what is already loaded.
 *  Overlapping entries are kept once; a gap or a mismatched overlap means the cursor is not trustworthy. */
export function mergePage(j: Journal | null, page: LedgerPage): Journal {
  const s = page.next - page.entries.length;
  if (s < 0) throw new Error("Invalid journal cursor");
  if (!j) return { start: s, next: page.next, entries: [...page.entries], digest: page.digest };
  if (s > j.next || page.next < j.start) throw new Error("Journal pages are not contiguous");
  const lo = Math.max(s, j.start), hi = Math.min(page.next, j.next);
  for (let n = lo; n < hi; n++) {
    if (page.entries[n - s].id !== j.entries[n - j.start].id) throw new Error("Journal changed under the cursor");
  }
  return {
    start: Math.min(s, j.start),
    next: Math.max(page.next, j.next),
    entries: [...page.entries.slice(0, Math.max(0, j.start - s)), ...j.entries, ...page.entries.slice(Math.max(0, j.next - s))],
    digest: page.next >= j.next ? page.digest : j.digest,
  };
}

/** The `after` cursor for the page just older than what is loaded, or null when the oldest entry is loaded. */
export const olderCursor = (j: Journal): number | null => (j.start === 0 ? null : Math.max(0, j.start - LEDGER_PAGE));
