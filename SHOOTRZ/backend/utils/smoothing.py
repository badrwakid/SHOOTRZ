from typing import List


def moving_average(series: List[float], window: int = 5) -> List[float]:
    if window <= 1 or len(series) == 0:
        return series
    out = []
    for i in range(len(series)):
        start = max(0, i - window + 1)
        window_vals = series[start : i + 1]
        out.append(sum(window_vals) / len(window_vals))
    return out








