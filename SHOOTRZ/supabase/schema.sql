-- Enable extensions
create extension if not exists "pgcrypto";
create extension if not exists "uuid-ossp";

-- Users
create table if not exists users (
  id uuid primary key default auth.uid(),
  email text unique not null,
  username text unique,
  name text,
  skill_level text,
  position text,
  auth_provider text not null default 'supabase',
  has_completed_onboarding boolean default false,
  created_at timestamptz not null default now()
);

-- Create index for faster username lookups
create index if not exists idx_users_username on users(username) where username is not null;

-- Videos
create table if not exists videos (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  file_url text not null,
  angle text,
  fps int,
  device text,
  created_at timestamptz not null default now()
);

-- Metrics
create table if not exists metrics (
  id uuid primary key default gen_random_uuid(),
  video_id uuid not null references videos(id) on delete cascade,
  metric_name text not null,
  value double precision not null,
  confidence double precision not null default 0,
  created_at timestamptz not null default now()
);

-- Feedback
create table if not exists feedback (
  id uuid primary key default gen_random_uuid(),
  metric_id uuid not null references metrics(id) on delete cascade,
  message text not null,
  severity text not null default 'info',
  created_at timestamptz not null default now()
);

-- Sessions
create table if not exists sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  timestamp timestamptz not null default now(),
  avg_score double precision
);

-- Models (optional)
create table if not exists models (
  id uuid primary key default gen_random_uuid(),
  version text not null,
  latency double precision,
  fps double precision,
  created_at timestamptz not null default now()
);

-- RLS
alter table users enable row level security;
alter table videos enable row level security;
alter table metrics enable row level security;
alter table feedback enable row level security;
alter table sessions enable row level security;

-- Policies
create policy "Users can read themselves" on users
  for select using (auth.uid() = id);

create policy "Users can insert themselves" on users
  for insert with check (auth.uid() = id);

create policy "Users can update themselves" on users
  for update using (auth.uid() = id) with check (auth.uid() = id);

create policy "Users can delete themselves" on users
  for delete using (auth.uid() = id);

create policy "User owns video rows" on videos
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "User owns metrics via video" on metrics
  for all using (
    exists(select 1 from videos v where v.id = metrics.video_id and v.user_id = auth.uid())
  ) with check (
    exists(select 1 from videos v where v.id = metrics.video_id and v.user_id = auth.uid())
  );

create policy "User owns feedback via metrics->video" on feedback
  for all using (
    exists(
      select 1 from metrics m
      join videos v on v.id = m.video_id
      where m.id = feedback.metric_id and v.user_id = auth.uid()
    )
  ) with check (
    exists(
      select 1 from metrics m
      join videos v on v.id = m.video_id
      where m.id = feedback.metric_id and v.user_id = auth.uid()
    )
  );

create policy "User owns sessions" on sessions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

