import json
import os
import random
import time
from pathlib import Path

from locust import HttpUser, between, events, task

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SAMPLE_VIDEOS = sorted(FIXTURE_DIR.glob("*.mp4"))

_error_count = {"total": 0, "by_status": {}}
_e2e_latencies = []
_e2e_successes = 0
_e2e_timeouts = 0


def _record_error(status):
    _error_count["total"] += 1
    key = str(status)
    _error_count["by_status"][key] = _error_count["by_status"].get(key, 0) + 1


@events.request.add_listener
def _on_request(request_type, name, response_time, response_length, response, exception, context, **kwargs):
    if exception is not None:
        _record_error("exception")
        return
    if response is not None and getattr(response, "status_code", 200) >= 400:
        _record_error(response.status_code)


class SubmitOnlyUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        if not SAMPLE_VIDEOS:
            raise RuntimeError(f"No .mp4 files found in {FIXTURE_DIR}")

    @task
    def submit(self):
        video = random.choice(SAMPLE_VIDEOS)
        with open(video, "rb") as f:
            self.client.post(
                "/mvp/analyze",
                files={"file": (video.name, f, "video/mp4")},
                data={"shooting_side": "right"},
                timeout=60,
                name="submit",
            )


class SubmitAndPollUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        if not SAMPLE_VIDEOS:
            raise RuntimeError(f"No .mp4 files found in {FIXTURE_DIR}")

    @task
    def submit_and_wait(self):
        global _e2e_successes, _e2e_timeouts
        video = random.choice(SAMPLE_VIDEOS)
        start = time.perf_counter()
        with open(video, "rb") as f:
            resp = self.client.post(
                "/mvp/analyze",
                files={"file": (video.name, f, "video/mp4")},
                data={"shooting_side": "right"},
                timeout=60,
                name="submit_with_poll",
            )
        if resp.status_code >= 400:
            _record_error(resp.status_code)
            return

        payload = resp.json()
        job_id = payload.get("job_id")
        if not job_id:
            _record_error("missing_job_id")
            return

        deadline = start + 60.0
        done = False
        while time.perf_counter() < deadline:
            poll = self.client.get(f"/mvp/result/{job_id}", name="poll", timeout=20)
            if poll.status_code >= 400:
                _record_error(poll.status_code)
                return
            status = poll.json().get("status")
            if status in {"completed", "failed"}:
                done = True
                break
            time.sleep(random.uniform(0.5, 1.0))

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if done:
            _e2e_successes += 1
            _e2e_latencies.append(elapsed_ms)
            events.request.fire(
                request_type="E2E",
                name="end_to_end",
                response_time=elapsed_ms,
                response_length=0,
                response=None,
                exception=None,
                context={},
            )
        else:
            _e2e_timeouts += 1
            _record_error("timeout")


def _percentile(values, pct):
    if not values:
        return None
    sorted_vals = sorted(values)
    idx = int(round((len(sorted_vals) - 1) * pct))
    return round(float(sorted_vals[idx]), 2)


@events.quitting.add_listener
def _write_report(environment, **kwargs):
    total = environment.stats.total
    submit_stats = environment.stats.get("submit", "POST")
    submit_poll_stats = environment.stats.get("submit_with_poll", "POST")

    report = {
        "num_requests": total.num_requests,
        "num_failures": total.num_failures,
        "error_rate_pct": round(total.num_failures / max(1, total.num_requests) * 100, 2),
        "queue_p50_ms": submit_stats.get_response_time_percentile(0.5) if submit_stats else None,
        "queue_p95_ms": submit_stats.get_response_time_percentile(0.95) if submit_stats else None,
        "queue_submit_poll_p50_ms": submit_poll_stats.get_response_time_percentile(0.5)
        if submit_poll_stats
        else None,
        "queue_submit_poll_p95_ms": submit_poll_stats.get_response_time_percentile(0.95)
        if submit_poll_stats
        else None,
        "end_to_end_p50_ms": _percentile(_e2e_latencies, 0.5),
        "end_to_end_p95_ms": _percentile(_e2e_latencies, 0.95),
        "end_to_end_completed": _e2e_successes,
        "end_to_end_timeouts": _e2e_timeouts,
        "completion_rate_pct": round(_e2e_successes / max(1, _e2e_successes + _e2e_timeouts) * 100, 2),
        "rps": round(total.total_rps, 2),
        "error_breakdown": _error_count["by_status"],
    }
    out_path = Path(os.getenv("LOCUST_REPORT_PATH", "load_report.json"))
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Load report written to {out_path}")
