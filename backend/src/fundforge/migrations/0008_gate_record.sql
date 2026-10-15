-- 0007: each generated room keeps its seed-free balance-gate record (attempt verdicts, failure names,
-- accepted policy labels and scores). Authored rooms store {}. Read only after the room finishes.
alter table rooms add column if not exists gate jsonb not null default '{}'::jsonb;
