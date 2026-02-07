"""Locust load test for the Click Tracker API.

Run the API first, then:

  # Web UI (open http://localhost:8089)
  uv run --extra load locust -f locustfile.py --host http://localhost:8080

  # Headless, 1000 users, 1000 spawn/s, 60s
  uv run --extra load locust -f locustfile.py --host http://localhost:8080 \\
    --users 1000 --spawn-rate 1000 --run-time 60s --headless

Example response time summary (POST /click), times in ms:

     Name        50%   66%   75%   90%   95%   99%  99.9%  100%   # reqs
  -------------- ----  ----  ----  ----  ----  ----  -----  -----  ------
  POST /click     35   110   180   320   420   980   1.8k   2k   59k
"""

import uuid
from datetime import datetime, timezone

from locust import task, constant_throughput
from locust.contrib.fasthttp import FastHttpUser


def _click_payload() -> dict:
    """Generate a random click payload."""
    return {
        "user_id": str(uuid.uuid4()),
        "shop_url": "https://example.com/shop",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        + "Z",
    }


class ClickTrackerUser(FastHttpUser):
    """Simulates a client posting click events."""

    # 1000 users × 1 task/s = 1000 req/s
    wait_time = constant_throughput(1)

    @task
    def track_click(self) -> None:
        """POST /click with a new random user_id each time."""
        with self.client.post(
            "/click",
            json=_click_payload(),
            name="/click",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                return
            if response.status_code == 0:
                response.failure("Connection error")
                return
            response.failure(f"HTTP {response.status_code}: {response.text}")
