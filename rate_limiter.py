import json
import os
from datetime import date

LIMIT_FILE = "rate_limits.json"
DAILY_LIMIT = 5


def _load() -> dict:
    if not os.path.exists(LIMIT_FILE):
        return {}
    with open(LIMIT_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(data: dict):
    with open(LIMIT_FILE, "w") as f:
        json.dump(data, f)


def _trusted_hops() -> int:
    """Number of reverse proxies in front of the app that append to X-Forwarded-For.

    Assumes Streamlit Community Cloud: one load balancer appends the address it
    saw as the right-most X-Forwarded-For entry. Anything to its left is
    client-supplied and must not be trusted. Override with TRUSTED_PROXY_HOPS.
    """
    try:
        return max(1, int(os.environ.get("TRUSTED_PROXY_HOPS", "1")))
    except ValueError:
        return 1


def client_ip_from_headers(headers) -> str:
    """Pick the client IP from the right-most trusted hop of X-Forwarded-For."""
    lowered = {str(k).lower(): v for k, v in dict(headers).items()}
    forwarded = lowered.get("x-forwarded-for", "")
    parts = [p.strip() for p in forwarded.split(",") if p.strip()]
    if parts:
        hops = _trusted_hops()
        return parts[-hops] if len(parts) >= hops else parts[0]
    return "unknown"


def get_client_ip(headers: dict) -> str:
    return client_ip_from_headers(headers)


def check_limit(ip: str) -> tuple[bool, int]:
    """Returns (allowed, runs_remaining)."""
    today = str(date.today())
    data = _load()
    entry = data.get(ip, {})

    if entry.get("date") != today:
        entry = {"date": today, "count": 0}

    remaining = DAILY_LIMIT - entry["count"]
    return remaining > 0, remaining


def record_run(ip: str):
    today = str(date.today())
    data = _load()
    entry = data.get(ip, {})

    if entry.get("date") != today:
        entry = {"date": today, "count": 0}

    entry["count"] += 1
    data[ip] = entry
    _save(data)
