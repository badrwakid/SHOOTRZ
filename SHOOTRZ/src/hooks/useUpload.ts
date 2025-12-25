import { useState, useCallback } from 'react'
import { uploadVideo } from '../services/supabase.storage'

export function useUpload(userId?: string) {
  const [progress, setProgress] = useState(0)

  const upload = useCallback(async (file: { uri: string; name: string; type: string; angle?: string; fps?: number; device?: string }) => {
    if (!userId) throw new Error('Missing userId')
    setProgress(10)
    const { file_url } = await uploadVideo(userId, file)
    setProgress(100)
    return { file_url }
  }, [userId])

  return { upload, progress }
}


