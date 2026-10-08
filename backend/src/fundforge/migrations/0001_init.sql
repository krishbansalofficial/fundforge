-- 0001: rooms, seats, append-only command log and journal
create table if not exists rooms (
  id text primary key,
  scenario text not null,
  tape_digest text not null,
  partners jsonb not null,
  names jsonb not null,
  version int not null default 0,
  created_at timestamptz not null default now()
);
create table if not exists seats (
  token_hash text primary key,
  room_id text not null references rooms(id),
  user_id text not null,
  role text not null
);
create table if not exists commands (
  room_id text not null references rooms(id),
  seq int not null,
  idem_key text not null,
  user_id text not null,
  command jsonb not null,
  result jsonb not null,
  created_at timestamptz not null default now(),
  primary key (room_id, seq),
  unique (room_id, idem_key)
);
create table if not exists journal_entries (
  room_id text not null references rooms(id),
  entry_id text not null,
  entity text not null,
  date date not null,
  memo text not null,
  postings jsonb not null,
  command_seq int not null,
  primary key (room_id, entry_id)
);
create or replace function forbid_change() returns trigger language plpgsql as $$
begin raise exception 'append-only table %', tg_table_name; end $$;
drop trigger if exists commands_append_only on commands;
create trigger commands_append_only before update or delete on commands
  for each row execute function forbid_change();
drop trigger if exists journal_append_only on journal_entries;
create trigger journal_append_only before update or delete on journal_entries
  for each row execute function forbid_change();
