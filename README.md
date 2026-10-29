# PhantomTrace
PhantomTrace is an AI-powered digital forensics investigation agent that analyses security logs, correlates evidence, reconstructs incident timelines, and generates verifiable forensic reports using Meta Muse Spark.

## Five-phase hackathon roadmap

| Phase | Deliverable | Status |
| --- | --- | --- |
| 1 | FastAPI backend and Muse Spark API integration | Complete |
| 2 | Log parser, event correlation, evidence reference verifier | Complete |
| 3 | Bounded Muse Spark tool-calling investigation and execution history | Implemented; live API smoke test pending |
| 4 | React dashboard, findings, tool activity and interactive timeline | Planned |
| 5 | Integration testing, deployment and three-minute demo | Planned |

## Run Phase 3

From `backend`, create a virtual environment and install `requirements-dev.txt`.
Copy `.env.example` to `.env` and set `MODEL_API_KEY` locally; never commit `.env`.
`META_MODEL` optionally overrides the default `muse-spark-1.3`.
Start with `python -m uvicorn app.main:app --reload`, then open
http://127.0.0.1:8000/docs and use `POST /api/investigate/agent`:

```json
{"logs":"EVT001 | 2026-10-28T02:12:00Z | PERMISSION_CHANGE | user=admin | role=administrator"}
```

The model chooses calls to `parse_logs`, `correlate_events`, and `verify_evidence`.
Each accepts `{}` and operates on server-owned evidence, so the model cannot
replace events. Calls execute in returned order; prerequisites are enforced.
Results return through Responses API `function_call_output` items with matching
call IDs and `previous_response_id`, following
[Meta's tool-calling documentation](https://dev.meta.ai/docs/tool-calling).
The response contains a structured report, original parsed events, correlation,
final report reference checks and tool history. Existing endpoints remain available.

The loop allows eight model turns and three tool calls per turn. Invalid tools,
arguments or ordering return tool errors for recovery. Premature completion,
invalid report JSON, nonexistent final references and exhausted limits fail with
HTTP 502. Invalid logs fail with HTTP 422 before contacting Meta. Provider errors
are sanitized. Each provider request uses the existing 30-second timeout and one
retry; the turn limit is not an overall wall-clock deadline.

Reference checks establish only that cited IDs exist, not that findings are true
or that all relevant evidence was cited. Review conclusions manually. Submitted
logs are sent to Meta; use synthetic data for the hackathon demo. Tool history is
returned to the caller and is not persisted or written to server logs.

## Test and review

From `backend`:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Tests use a mocked Muse Spark client and need no API key or network. Before merging
`feature/agentic-investigation`, run a live synthetic-log smoke test with your local
key and inspect the report, tool history and reference checks. Keep `main` stable
until review; no live provider call is part of the automated test suite.
