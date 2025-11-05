import { useState, useCallback } from 'react'
import { uploadVideo } from '../services/supabase.storage'
import { analyzeJson } from '../services/fastapi.service'

export function useUpload(userId?: string) {
  const [progress, setProgress] = useState(0)
  const [jobId, setJobId] = useState<string | null>(null)

  const upload = useCallback(async (file: { uri: string; name: string; type: string; angle?: string; fps?: number; device?: string }) => {
    if (!userId) throw new Error('Missing userId')
    setProgress(10)
    const { file_url } = await uploadVideo(userId, file)
    setProgress(60)
    const resp = await analyzeJson({ user_id: userId, file_url, angle: file.angle, fps: file.fps, device: file.device })
    setProgress(100)
    setJobId(resp.job_id)
    return resp
  }, [userId])

  return { upload, progress, jobId }
}


