-- 0004: each room secretly draws a market variant; revealed only in the debrief.
alter table rooms add column if not exists variant text not null default 'base';
