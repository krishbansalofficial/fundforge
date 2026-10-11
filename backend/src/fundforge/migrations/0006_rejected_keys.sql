-- 0006: a rejected command's outcome is bound to its idempotency key, so a retry with the
-- same key returns the same rejection instead of being re-evaluated against later state.
-- Not part of the replayed log: rejections change no economics.
create table if not exists rejected_commands (
  room_id text not null references rooms(id),
  idem_key text not null,
  user_id text not null,
  command jsonb not null,
  message text not null,
  room_version int not null,
  created_at timestamptz not null default now(),
  primary key (room_id, idem_key)
);
drop trigger if exists rejected_append_only on rejected_commands;
create trigger rejected_append_only before update or delete on rejected_commands
  for each row execute function forbid_change();
