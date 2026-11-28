-- 0009: short, single-use join codes for the open seat of a two-player room. The code is a lobby
-- convenience only: claiming it rotates that seat's token, so the code itself never authorizes play.
create table if not exists join_codes (
  code text primary key,
  room_id text not null references rooms(id),
  role text not null check (role in ('pm', 'mp')),
  created_at timestamptz not null default now(),
  claimed_at timestamptz
);
create index if not exists join_codes_room on join_codes (room_id);
