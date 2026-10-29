
from collections import Counter
from datetime import datetime, timedelta


def correlate_events(events: list) -> dict:
    ordered = sorted(
        events,
        key=lambda e: datetime.fromisoformat(e["timestamp"])
    )

    users = Counter()
    ips = Counter()
    findings = []

    for event in ordered:
        if event.get("user"):
            users[event["user"]] += 1
        if event.get("ip"):
            ips[event["ip"]] += 1

    # Detect 3+ login failures from the same user/IP
    # within 60 seconds followed by a successful login.
    for index, event in enumerate(ordered):
        if event["event_type"] != "LOGIN_SUCCESS":
            continue

        success_time = datetime.fromisoformat(
            event["timestamp"]
        )

        failures = [
            previous for previous in ordered[:index]
            if previous["event_type"] == "LOGIN_FAILED"
            and previous.get("user") == event.get("user")
            and previous.get("ip") == event.get("ip")
            and (
                success_time - timedelta(seconds=60)
                <= datetime.fromisoformat(
                    previous["timestamp"]
                )
                <= success_time
            )
        ]

        if len(failures) >= 3:
            findings.append({
                "type": "FAILED_LOGINS_THEN_SUCCESS",
                "severity": "medium",
                "description": (
                    "Multiple failed logins followed "
                    "by successful authentication."
                ),
                "event_ids": [
                    e["event_id"] for e in failures
                ] + [event["event_id"]],
                "user": event.get("user"),
                "ip": event.get("ip"),
            })

    # Identify permission changes for manual review.
    for event in ordered:
        if event["event_type"] == "PERMISSION_CHANGE":
            findings.append({
                "type": "PERMISSION_CHANGE_REVIEW",
                "severity": "medium",
                "description": (
                    "Permission modification detected; "
                    "authorization requires verification."
                ),
                "event_ids": [event["event_id"]],
                "user": event.get("user"),
                "ip": event.get("ip"),
            })

    return {
        "event_count": len(ordered),
        "users": dict(users),
        "ip_addresses": dict(ips),
        "findings": findings,
        "finding_count": len(findings),
    }
