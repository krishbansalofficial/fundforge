-- 0003: real-time clock scheduling. Wall-clock fields only decide WHEN the server logs a tick.
alter table rooms add column if not exists running boolean not null default false;
alter table rooms add column if not exists speed int not null default 0;
alter table rooms add column if not exists next_tick_at timestamptz;
create index if not exists rooms_due on rooms (next_tick_at) where running;
