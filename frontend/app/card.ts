// Shareable ending card text from a completed run's server fields. Mirrors game/scripts/card_rules.gd row for
// row, so both clients show the same facts. Nothing here computes money, score or rank; a value the server did
// not send is left out or shown as "?", never guessed.
import { exactPct, type Debrief, type Outcome } from "./lib.ts";

export const LABELS: Record<string, string> = {
  WIN: "Win", SURVIVAL: "Survival", DISTRESS: "Distress",
  RENEWAL: "Renewal", WINDDOWN: "Winddown", DEFAULT: "Default", COMPANY_FAILURE: "Company failure",
};
export const label = (o: Outcome) => LABELS[o.label] ?? o.label;

export type Verify = { rules_version?: string; chain_head?: string };
export type Row = [string, string];

const signed = (s: string | null | undefined) => (s == null ? "+?" : s.startsWith("-") ? s : `+${s}`);

/** A decimal string as dollars. String-only, so no float rounding: every digit the server sent is kept (at least cents). */
export function exactMoney(s: string): string {
  const t = s.trim();
  const [whole, frac = ""] = t.replace(/^-/, "").split(".");
  return `${t.startsWith("-") ? "-" : ""}$${whole.replace(/\B(?=(\d{3})+$)/g, ",")}.${frac.padEnd(2, "0")}`;
}

/** What the run's market was, from the revealed `variant`; Case 1's day 16 text would be wrong elsewhere. */
export function marketText(variant: string | null | undefined, scenario?: string | null): string {
  const v = variant ?? "base";
  if (scenario != null && !scenario.startsWith("case1")) return `The ${scenario} run's hidden variant was "${v}".`;
  if (v === "base") return "The day 16 market was a sell-off and short squeeze. You couldn't know which in advance.";
  if (v === "rally") return "The day 16 market was a broad rally. You couldn't know which in advance.";
  if (v.startsWith("seed:")) return `A generated market: Case 1's crisis calendar on a seeded price path. Seed revealed: ${v.slice(5)}`;
  return `The market was the hidden "${v}" variant.`;
}

/** `seedHash` is this client's SHA-256 of the revealed seed; absent where the browser has no crypto.subtle
 *  (a plain-http origin), and then the served commitment is shown unchecked. */
export function cardRows(o: Outcome, names: Record<string, string>, research?: Debrief["research"], verify?: Verify, seedHash?: string): Row[] {
  const rows: Row[] = [["Partners", `${names.pm ?? "?"} (PM) and ${names.mp ?? "?"} (MP)`]];
  const score = `Score ${signed(o.score)} bps`;
  rows.push(["Result", o.rank != null && o.funds != null ? `#${o.rank} of ${o.funds} funds  /  ${score}` : score]);
  rows.push(["vs benchmark", `fund ${signed(o.fund_return_bps)} bps vs passive book ${signed(o.benchmark_return_bps)} bps`]);
  rows.push(["Final NAV", exactMoney(o.nav ?? "0")]);
  rows.push(["Forced actions", String((o.forced ?? []).length)]);
  const brier = (["pm", "mp"] as const).flatMap((role) => {
    const seat = research?.seats?.[role];
    return seat && seat.theses > 0 && seat.mean_brier != null ? [`${role.toUpperCase()} ${seat.mean_brier} (${seat.theses})`] : [];
  });
  if (brier.length) rows.push(["Mean Brier", brier.join("  ")]);
  if (o.max_drawdown != null) rows.push(["Max drawdown", `${exactPct(o.max_drawdown) ?? o.max_drawdown}% (NAV per unit, at closes)`]);
  if (o.scenario != null) rows.push(["Scenario", o.scenario]);
  if (o.generated_days != null && o.stressed_days != null) rows.push(["Stressed days", `${o.stressed_days} of ${o.generated_days} generated`]);
  const variant = o.variant ?? "base";
  if (variant.startsWith("seed:")) {
    rows.push(["Seed", variant.slice(5)]);
    const served = o.seed_commitment ?? seedHash;
    if (served) rows.push(["Seed SHA-256", seedHash && seedHash !== served ? `${served} (does NOT match the revealed seed: ${seedHash})` : served]);
  } else {
    rows.push(["Variant", variant]);
  }
  if (verify?.rules_version != null) rows.push(["Rules", verify.rules_version]);
  if (verify?.chain_head != null) rows.push(["Chain head", verify.chain_head]);
  rows.push(["Journal", o.journal_digest ?? "?"]);
  return rows;
}

export const cardText = (o: Outcome, rows: Row[]) =>
  [`FundForge: ${label(o)}`, marketText(o.variant, o.scenario), ...rows.map(([k, v]) => `${k}: ${v}`), "Fictional fund; no real money."].join("\n");
