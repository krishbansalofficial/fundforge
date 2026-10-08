-- 0002: pin rules per room, hash-chain the command log, and let SQL itself check the books.
alter table rooms add column if not exists rules_version text not null default 'case1-rules-2026.10.0';
alter table commands add column if not exists journal_digest_after text;
alter table commands add column if not exists chain_hash text;

create table if not exists journal_lines (
  room_id text not null,
  entry_id text not null,
  line_no int not null,
  entity text not null,
  account text not null,
  amount numeric(20, 2) not null check (amount <> 0),
  primary key (room_id, entry_id, line_no),
  foreign key (room_id, entry_id) references journal_entries (room_id, entry_id)
);

-- Every entry must have >= 2 lines summing to zero, checked at COMMIT so lines can be inserted one by one.
create or replace function check_entry_balanced() returns trigger language plpgsql as $$
declare n int; total numeric;
begin
  select count(*), coalesce(sum(amount), 0) into n, total
    from journal_lines where room_id = new.room_id and entry_id = new.entry_id;
  if n < 2 or total <> 0 then
    raise exception 'unbalanced journal entry %/% (lines %, sum %)', new.room_id, new.entry_id, n, total;
  end if;
  return null;
end $$;
drop trigger if exists journal_lines_balanced on journal_lines;
create constraint trigger journal_lines_balanced after insert on journal_lines
  deferrable initially deferred for each row execute function check_entry_balanced();

drop trigger if exists journal_lines_append_only on journal_lines;
create trigger journal_lines_append_only before update or delete on journal_lines
  for each row execute function forbid_change();
drop trigger if exists commands_no_truncate on commands;
create trigger commands_no_truncate before truncate on commands for each statement execute function forbid_change();
drop trigger if exists journal_no_truncate on journal_entries;
create trigger journal_no_truncate before truncate on journal_entries for each statement execute function forbid_change();
drop trigger if exists lines_no_truncate on journal_lines;
create trigger lines_no_truncate before truncate on journal_lines for each statement execute function forbid_change();

create or replace view trial_balance as
  select room_id, entity, account, sum(amount) as balance
  from journal_lines group by room_id, entity, account;
