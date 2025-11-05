import { useEffect, useState } from 'react'
import { getResult } from '../services/fastapi.service'

type Metric = { metric_name: string; value: number; confidence: number }
type FeedbackItem = { message: string; severity?: string }

export function useRealtime(jobId: string | null) {
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [feedback, setFeedback] = useState<FeedbackItem[]>([])
  const [status, setStatus] = useState<string>('idle')

  useEffect(() => {
    if (!jobId) return
    let cancelled = false
    setStatus('queued')
    const interval = setInterval(async () => {
      try {
        const res = await getResult(jobId)
        if (cancelled) return
        setStatus(res.status)
        if (res.metrics) setMetrics(res.metrics)
        if (res.feedback) setFeedback(res.feedback)
        if (res.status === 'completed') clearInterval(interval)
      } catch {}
    }, 1000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [jobId])

  return { status, metrics, feedback }
}


