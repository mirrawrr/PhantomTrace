
import ipaddress
from datetime import datetime
from typing import Any


def parse_security_logs(raw_logs: str) -> dict[str, Any]:
    events = []
    errors = []
    seen_ids = set()

    if not raw_logs.strip():
        return {
            "events": [],
            "errors": ["No log data provided."],
            "total_events": 0,
        }

    for line_number, line in enumerate(
        raw_logs.splitlines(), start=1
    ):
        line = line.strip()
        if not line:
            continue

        parts = [part.strip() for part in line.split("|")]

        if len(parts) < 4:
            errors.append(
                f"Line {line_number}: Expected ID, timestamp, "
                "event type and at least one field."
            )
            continue

        event_id, timestamp, event_type = parts[:3]

        if not event_id or not event_type:
            errors.append(
                f"Line {line_number}: Missing event ID or type."
            )
            continue

        if event_id in seen_ids:
            errors.append(
                f"Line {line_number}: Duplicate ID {event_id}."
            )
            continue

        try:
            dt = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )
            if dt.tzinfo is None:
                raise ValueError("Timezone is required")
        except ValueError:
            errors.append(
                f"Line {line_number}: Invalid timestamp."
            )
            continue

        fields = {}
        invalid_field = False

        for item in parts[3:]:
            if "=" not in item:
                invalid_field = True
                break

            key, value = item.split("=", 1)
            key = key.strip().lower()
            value = value.strip()

            if not key or not value or key in fields:
                invalid_field = True
                break

            fields[key] = value

        if invalid_field:
            errors.append(
                f"Line {line_number}: Invalid event fields."
            )
            continue

        if "ip" in fields:
            try:
                ipaddress.ip_address(fields["ip"])
            except ValueError:
                errors.append(
                    f"Line {line_number}: Invalid IP address."
                )
                continue

        events.append({
            "event_id": event_id,
            "timestamp": dt.isoformat(),
            "event_type": event_type.upper(),
            "user": fields.get("user"),
            "ip": fields.get("ip"),
            "fields": fields,
            "raw": line,
        })

        seen_ids.add(event_id)

    events.sort(
        key=lambda event: event["timestamp"]
    )

    return {
        "events": events,
        "errors": errors,
        "total_events": len(events),
    }