export type Metric = { metric_name: string; value: number; confidence: number }

export function toScore(metrics: Metric[]): number {
  if (!metrics.length) return 0
  return metrics.reduce((a, m) => a + m.value, 0) / metrics.length
}








