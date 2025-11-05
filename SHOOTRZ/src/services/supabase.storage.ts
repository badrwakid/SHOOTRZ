import { supabase } from './supabase.client'

export async function uploadVideo(userId: string, file: { uri: string; name: string; type: string }) {
  const path = `${userId}/${Date.now()}-${file.name}`
  // In Expo, convert to a fetch-compatible body or use the FileSystem to read as Blob
  const res = await supabase.storage.from('videos').upload(path, {
    uri: file.uri,
    name: file.name,
    type: file.type,
  } as any)
  if (res.error) throw res.error
  const signed = await supabase.storage.from('videos').createSignedUrl(path, 60 * 60)
  return { file_url: signed.data?.signedUrl as string, storage_path: path }
}








