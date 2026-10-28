
def verify_evidence(
    events: list,
    findings: list
) -> dict:
    valid_ids = {
        event["event_id"] for event in events
    }

    results = []

    for finding in findings:
        referenced_ids = finding.get("event_ids", [])

        missing_ids = [
            event_id for event_id in referenced_ids
            if event_id not in valid_ids
        ]

        results.append({
            "finding_type": finding.get("type"),
            "referenced_ids": referenced_ids,
            "missing_ids": missing_ids,
            "references_valid": (
                bool(referenced_ids)
                and len(missing_ids) == 0
            ),
        })

    return {
        "verified_references": sum(
            result["references_valid"]
            for result in results
        ),
        "total_findings": len(results),
        "results": results,
    }
