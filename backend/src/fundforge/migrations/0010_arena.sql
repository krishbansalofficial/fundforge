-- 0010: Arena accounts, verified results and the weekly digest. None of this is game state: the engine never
-- reads it, and a result row is written only after the room replays and verifies from its command log.
create table if not exists users (
  id text primary key,
  email text not null unique,
  display_name text not null,
  created_at timestamptz not null default now()
);
create table if not exists login_tokens (  -- magic links: single use, short-lived, stored hashed
  token_hash text primary key,
  email text not null,
  created_at timestamptz not null default now(),
  used_at timestamptz
);
create table if not exists account_sessions (
  token_hash text primary key,
  user_id text not null references users(id),
  expires_at timestamptz not null
);
create table if not exists room_players (  -- which account sat in which seat; guests have no row
  room_id text not null references rooms(id),
  role text not null check (role in ('pm', 'mp')),
  user_id text not null references users(id),
  primary key (room_id, role)
);
create index if not exists room_players_user on room_players (user_id);
create table if not exists results (
  room_id text primary key references rooms(id),
  scenario text not null,
  label text not null,
  score numeric not null,
  excess_bps numeric not null,
  nav numeric not null,
  solo boolean not null,
  journal_digest text not null,
  chain_head text not null,
  rules_version text not null,
  verified_at timestamptz not null default now()
);
create index if not exists results_board on results (scenario, score desc);
create table if not exists digest_runs (  -- one weekly digest per ISO week, however often the job runs
  week text primary key,
  sent int not null,
  ran_at timestamptz not null default now()
);
