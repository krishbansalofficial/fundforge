-- 0005: solo rooms with a deterministic bot partner (owner decision, 8 Oct 2026).
alter table rooms add column if not exists bot_role text;
