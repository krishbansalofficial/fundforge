/** Campaign prospect and winddown helpers. Every figure comes from the seat's own view; the server re-checks all of it. */

/** The amounts a joint admission may bind: each positive multiple of `step` up to `escrow`, largest first.
 *  Whole-dollar strings only (the campaign fixture's are); anything else gives no choices rather than a guess. */
export function admissionAmounts(escrow: string, step: string | null): string[] {
  const whole = /^\d{1,15}$/; // exact as a JS number
  if (!step || !whole.test(escrow) || !whole.test(step) || Number(step) === 0) return [];
  const out: string[] = [];
  for (let k = Math.floor(Number(escrow) / Number(step)); k > 0; k--) out.push(String(k * Number(step)));
  return out;
}

const usd = (s: unknown) => `$${Number(s).toLocaleString("en-US")}`;

/** One line for a winddown or admission package the partner is asked to sign; null for other kinds. */
export function packageTerms(kind: string, terms: Record<string, unknown>): string | null {
  if (kind === "winddown") return `Controlled winddown from day ${terms.day}: no new buying or shorting; liquidate the book so every unit is redeemed. This ends the campaign.`;
  if (kind === "admission") return `Admit ${terms.series} for ${usd(terms.amount)} at the day ${terms.deal_day} dealing close, issue price ${terms.issue_price}, high-water mark ${terms.hwm}, subject to certification and post-flow checks.`;
  return null;
}
