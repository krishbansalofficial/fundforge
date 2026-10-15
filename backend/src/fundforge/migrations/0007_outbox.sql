-- 0007: transactional outbox (docs/ML_CONTRACTS.md section 3, ml/contracts/outbox_event.schema.json).
-- Written in the same transaction as each accepted command; Debezium relays it to Kafka.
-- Downstream only: nothing in the game reads it, and replay never depends on it.
create table if not exists outbox (
  event_id uuid primary key,
  contract_version text not null,
  room_id text not null references rooms(id),
  seq int not null check (seq >= 1),
  idx int not null check (idx >= 0),
  kind text not null check (kind in ('command', 'journal_entry', 'observation', 'notice', 'incident', 'outcome')),
  audience text not null check (audience in ('public', 'pm', 'mp', 'internal')),
  rules_version text not null,
  tape_digest text not null,
  day int not null,
  phase text not null,
  sim_date date not null,
  chain_head text not null,
  payload jsonb not null,
  created_at timestamptz not null default now(),
  unique (room_id, seq, idx),
  foreign key (room_id, seq) references commands (room_id, seq)
);
drop trigger if exists outbox_append_only on outbox;
create trigger outbox_append_only before update or delete on outbox
  for each row execute function forbid_change();
drop trigger if exists outbox_no_truncate on outbox;
create trigger outbox_no_truncate before truncate on outbox for each statement execute function forbid_change();
