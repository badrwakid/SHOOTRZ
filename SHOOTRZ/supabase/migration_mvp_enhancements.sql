-- MVP Enhancements Migration
-- Adds camera_angle enum, unit column to metrics, session_videos table, and models table enhancements

-- Create camera angle enum
do $$ begin
	create type camera_angle_type as enum (
		'front_side_45',
		'side',
		'behind',
		'front',
		'overhead',
		'unknown'
	);
exception
	when duplicate_object then null;
end $$;

-- Add camera_angle column to videos table if it doesn't exist
do $$ begin
	if not exists (
		select 1 from information_schema.columns
		where table_name = 'videos' and column_name = 'camera_angle'
	) then
		alter table videos add column camera_angle camera_angle_type default 'unknown';
	end if;
end $$;

-- Add unit column to metrics table if it doesn't exist
do $$ begin
	if not exists (
		select 1 from information_schema.columns
		where table_name = 'metrics' and column_name = 'unit'
	) then
		alter table metrics add column unit text;
	end if;
end $$;

-- Add phase column to metrics table if it doesn't exist
do $$ begin
	if not exists (
		select 1 from information_schema.columns
		where table_name = 'metrics' and column_name = 'phase'
	) then
		alter table metrics add column phase text;
	end if;
end $$;

-- Add frame_idx column to metrics table if it doesn't exist
do $$ begin
	if not exists (
		select 1 from information_schema.columns
		where table_name = 'metrics' and column_name = 'frame_idx'
	) then
		alter table metrics add column frame_idx integer;
	end if;
end $$;

-- Create session_videos junction table if it doesn't exist
create table if not exists session_videos (
	session_id uuid not null references sessions(id) on delete cascade,
	video_id uuid not null references videos(id) on delete cascade,
	primary key (session_id, video_id)
);

-- Create index on session_videos for faster lookups
create index if not exists idx_session_videos_session_id on session_videos(session_id);
create index if not exists idx_session_videos_video_id on session_videos(video_id);

-- Enhance models table with additional columns if they don't exist
do $$ begin
	-- Add name column
	if not exists (
		select 1 from information_schema.columns
		where table_name = 'models' and column_name = 'name'
	) then
		alter table models add column name text not null default 'unknown';
	end if;

	-- Add description column
	if not exists (
		select 1 from information_schema.columns
		where table_name = 'models' and column_name = 'description'
	) then
		alter table models add column description text;
	end if;

	-- Add mpjpe column (Mean Per Joint Position Error)
	if not exists (
		select 1 from information_schema.columns
		where table_name = 'models' and column_name = 'mpjpe'
	) then
		alter table models add column mpjpe double precision;
	end if;

	-- Add pa_mpjpe column (Procrustes Aligned MPJPE)
	if not exists (
		select 1 from information_schema.columns
		where table_name = 'models' and column_name = 'pa_mpjpe'
	) then
		alter table models add column pa_mpjpe double precision;
	end if;
end $$;

-- Add recorded_at column to videos if it doesn't exist
do $$ begin
	if not exists (
		select 1 from information_schema.columns
		where table_name = 'videos' and column_name = 'recorded_at'
	) then
		alter table videos add column recorded_at timestamptz;
	end if;
end $$;

-- Add device_info JSONB column to videos if it doesn't exist
do $$ begin
	if not exists (
		select 1 from information_schema.columns
		where table_name = 'videos' and column_name = 'device_info'
	) then
		alter table videos add column device_info jsonb;
	end if;
end $$;

-- Enable RLS on session_videos
alter table session_videos enable row level security;

-- Create RLS policy for session_videos
create policy "User owns session_videos via sessions" on session_videos
	for all using (
		exists(
			select 1 from sessions s
			where s.id = session_videos.session_id and s.user_id = auth.uid()
		)
	) with check (
		exists(
			select 1 from sessions s
			where s.id = session_videos.session_id and s.user_id = auth.uid()
		)
	);

-- Create index on metrics for faster queries by metric_name
create index if not exists idx_metrics_metric_name on metrics(metric_name);

-- Create index on metrics for faster queries by phase
create index if not exists idx_metrics_phase on metrics(phase) where phase is not null;

-- Create index on videos for faster queries by camera_angle
create index if not exists idx_videos_camera_angle on videos(camera_angle);

-- Add title and date columns to sessions if they don't exist
do $$ begin
	if not exists (
		select 1 from information_schema.columns
		where table_name = 'sessions' and column_name = 'title'
	) then
		alter table sessions add column title text;
	end if;

	if not exists (
		select 1 from information_schema.columns
		where table_name = 'sessions' and column_name = 'date'
	) then
		alter table sessions add column date date;
	end if;
end $$;



