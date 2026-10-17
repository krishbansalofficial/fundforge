// Shareable ending card: pure text from a completed run's server fields (mirrors Godot CardRules.rows).
// Nothing here computes money, return, score or rank; absent fields are left out, never guessed.
import { exactPct, money, type Outcome } from "./lib.ts";

export const LABELS: Record<string, string> = { WIN: "Win", SURVIVAL: "Survival", DISTRESS: "Distress" };
const signed = (s: string) => (s.startsWith("-") ? s : `+${s}`);

/** `seedHash` is the client's SHA-256 of the revealed seed, when there is one; it must match the commitment. */
export function cardRows(o: Outcome, names: Record<string, string>, rulesVersion: string, seedHash?: string): [string, string][] {
  const rows: [string, string][] = [
    ["Partners", `${names.pm ?? "?"} (PM) and ${names.mp ?? "?"} (MP)`],
    ["Result", `${LABELS[o.label] ?? o.label}, #${o.rank} of ${o.funds} funds, score ${signed(o.score)} bps`],
    ["vs benchmark", `fund ${signed(o.fund_return_bps)} bps vs passive book ${signed(o.benchmark_return_bps)} bps (excess ${signed(o.excess_bps)} bps)`],
    ["Final NAV", money(o.nav, 2)],
    ["Max drawdown", `${exactPct(o.max_drawdown) ?? o.max_drawdown}% (NAV per unit, at closes)`],
    ["Scenario", o.scenario],
  ];
  if (o.variant.startsWith("seed:")) {
    rows.push(["Seed", o.variant.slice(5)]);
    const served = o.seed_commitment ?? seedHash;
    if (served) rows.push(["Seed SHA-256", seedHash && seedHash !== served ? `${served} (does NOT match the revealed seed: ${seedHash})` : served]);
  } else {
    rows.push(["Variant", o.variant]);
  }
  rows.push(["Rules", rulesVersion], ["Journal", o.journal_digest]);
  return rows;
}

export const cardText = (o: Outcome, rows: [string, string][]) =>
  [`FundForge: ${LABELS[o.label] ?? o.label}`, ...rows.map(([k, v]) => `${k}: ${v}`), "Fictional fund; no real money."].join("\n");
