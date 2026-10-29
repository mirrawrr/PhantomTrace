# PhantomTrace
PhantomTrace is an AI-powered digital forensics investigation agent that analyses security logs, correlates evidence, reconstructs incident timelines, and generates verifiable forensic reports using Meta Muse Spark.

## Five-phase hackathon roadmap

| Phase | Deliverable | Status |
| --- | --- | --- |
| 1 | FastAPI backend and Muse Spark API integration | Complete |
| 2 | Log parser, event correlation, evidence reference verifier | Complete |
| 3 | Bounded Muse Spark tool-calling investigation and execution history | Implemented; live API smoke test pending |
| 4 | React dashboard, findings, tool activity and interactive timeline | Implemented; local end-to-end check pending |
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

## Phase 4: investigation dashboard

The React dashboard lives in `frontend/` and uses the existing agent endpoint.
Use Node.js 22.12 or newer. Open two terminals in the repository root.

Terminal 1 (backend, with the Phase 3 environment and local API key):

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Terminal 2 (dashboard):

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL Vite prints (normally http://127.0.0.1:5173). The development
server proxies `/api` and `/health` to FastAPI on port 8000, so no CORS change or
browser API key is needed. `Load sample` fills synthetic logs; it does not invent
results. Click `Start investigation` to run the live agent. Use findings' event-ID
buttons to open the corresponding timeline evidence, filter events, expand actual
tool results, or export the complete investigation JSON. Cancel stops the browser's
request; it does not guarantee cancellation of a provider request already running.
Reports and logs stay in memory in the browser, with no browser storage. The export
contains source logs; handle it as evidence. Editing the intake does not change a
completed report, which continues to represent the last submitted evidence.

Run dashboard checks from `frontend` with `npm test` and `npm run build`.
Tests cover request shape, cancellation, validation errors, response failures and
chronological event filtering. GitHub Actions runs the tests and production build.
Live acceptance: load sample, investigate, check five events and both correlation
patterns, open an event from a finding, filter the timeline, inspect three tool
results, and export JSON. Also stop FastAPI and verify a readable error is shown.
The app shows actual returned findings; the model may summarize patterns differently.

This phase is for local development. A production host must route `/api` and
`/health` to FastAPI on the same origin; Vite's development proxy is not part of
the production build. Deployment and access controls are Phase 5 work.
