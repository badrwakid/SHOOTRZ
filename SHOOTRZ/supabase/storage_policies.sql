-- Storage policies for `videos` bucket
-- Create the bucket in Dashboard → Storage first.

-- Users can read their own files under folder user_id/
create policy "User read own videos" on storage.objects
  for select using (
    bucket_id = 'videos' and
    (auth.role() = 'authenticated') and
    (split_part(name, '/', 1) = auth.uid()::text)
  );

-- Users can write files under user_id/
create policy "User write own videos" on storage.objects
  for insert with check (
    bucket_id = 'videos' and
    (auth.role() = 'authenticated') and
    (split_part(name, '/', 1) = auth.uid()::text)
  );

-- Users can delete their own files
create policy "User delete own videos" on storage.objects
  for delete using (
    bucket_id = 'videos' and
    (auth.role() = 'authenticated') and
    (split_part(name, '/', 1) = auth.uid()::text)
  );
