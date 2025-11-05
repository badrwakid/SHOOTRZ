export function movingAverage(series: number[], window = 5): number[] {
  if (window <= 1 || series.length === 0) return series
  const out: number[] = []
  for (let i = 0; i < series.length; i++) {
    const start = Math.max(0, i - window + 1)
    const slice = series.slice(start, i + 1)
    out.push(slice.reduce((a, b) => a + b, 0) / slice.length)
  }
  return out
}








