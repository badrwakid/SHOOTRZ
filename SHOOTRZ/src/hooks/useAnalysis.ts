import { useMemo } from 'react'

export function useAnalysis(metrics: { metric_name: string; value: number }[]) {
  const score = useMemo(() => {
    if (!metrics.length) return 0
    const vals = metrics.map((m) => m.value)
    return vals.reduce((a, b) => a + b, 0) / vals.length
  }, [metrics])
  return { score }
}








