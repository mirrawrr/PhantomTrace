# Case console

The console presents the evidence timeline and actual execution feed ahead of the
long narrative. It preserves source inspection, filters, JSON export, witness
checks and the labelled original recording. It changes no production credentials,
hosting plan or budget defaults.

## Layout and meaning

- The scoreboard derives counts from the returned report, never fixed demo values.
  Green means explained by a supplied record, amber means review, red means
  unresolved. A matching record is not independently authenticated authorization.
- The cyan reference count checks cited ID existence, not the truth of a finding.
  Source-return markers mean actual tool output, not that an entire narrative is
  verified. A tool PASS applies only to that tool's submitted structured checks.
- The horizontal UTC timeline is always visible. Keyboard-focusable event buttons
  open the source. Finding selectors highlight their cited events and clear filters.
  An event associated with multiple dispositions takes the highest review priority:
  unresolved, then review, then record match. Search/type filters remain available.
- Finding observations remain visible. Assessments, alternatives, next evidence
  and structured fact details are collapsed. One next-actions section uses the
  handoff actions when available, otherwise recommendations; the limitations are
  in one footer. Summary and open questions remain inspectable.
- Intake collapses when a full investigation begins. A cancel button remains in
  the console header. Cancelling the browser does not guarantee stopping the
  provider or its billing. Inputs can be reopened; a run uses its submitted snapshot.
- Barlow Condensed and JetBrains Mono load from Google Fonts with system fallbacks.
  Body/source text starts at 16px, with high-contrast labels and explicit verdict
  words alongside colors. Desktop activity stays at the right; mobile stacks it.

## Honest streaming

Adaptive mode POSTs to `/api/investigate/adaptive/stream` with the same credentials
and request body as the existing JSON route. This route is covered by the existing
hosted authentication, request-count limits, size limit and provider-dollar budget.
One click is one investigation; there is no second polling/model request.

The server emits SSE frames:

1. `workspace`: events the parser actually produced.
2. `tool`: the actual completed call ID, tool, purpose and result, immediately
   after execution. No private reasoning, generated progress or invented steps.
3. `result`: the same final validated report as the JSON endpoint, including
   optional witness checking. Final scoreboard counts appear only now.
4. `error`: an allowlisted category and sanitized message instead of a result.

Before a final report, timeline colors distinguish parsed/pending events, events
returned by tools and actual supplied-record matches. These provisional states
are labelled; they are not final finding dispositions. Finding cards are not
fabricated early just to animate amber-to-green. The actual lookup transition can
change an event marker to green. Completed calls remain visible after failure or
disconnection; no incomplete stream becomes a successful report.

Transitions for evidence markers, findings and feed entries are 180–200ms.
`prefers-reduced-motion` disables animation and transitions. Marker appearance is
triggered by real returned event IDs. Final reference-count entry is triggered by
the validated response. No timer simulates activity.

Fixed-pipeline mode keeps the existing JSON request and displays its actual
executions after completion; it does not claim live streaming. Replay retains its
visible recording banner and older five-event provenance.

## Checks and live acceptance

Tests cover streaming order, callback/tool-history consistency, failed and
truncated streams, same-request authentication/cancellation, the body wrapper's
disconnect forwarding, verdict priority and non-duplicated action sources. The
production HTTP test checks stream authentication and no-store headers with a
fake investigator; no real Meta request is used in CI.

The build and server-side component render are checked locally. Local browser
preview was attempted but its port was unreachable in the desktop environment;
visual acceptance remains required. On the feature branch, restart the backend
and frontend, then review at 1280×720 and a narrow/mobile width:

- Replay first: five events, two review findings and an explicit recorded banner.
- Live mixed case: parsed events appear, then real tool entries; record-match
  color changes happen only after lookup output, with final counts from the report.
- Select a finding and verify exactly its IDs highlight. Open EVT005 source.
- Cancel a run: keep actual received activity and show no final verdict.
- Enable reduced motion and confirm the same information without movement.
- Confirm voice upload and separate witness checking remain accessible in intake.

Render Free still has cold starts. Streaming does not make it always-on or make
its ephemeral budget ledger durable. No paid upgrade or persistent disk has been
provisioned by this change. A hosted SSE acceptance run is still needed after a
reviewed merge and manual deployment.

## Provider HTTP diagnostics

A local streamed run returned `provider_http_error`; its original status and cause were not retained. Failures now include a numeric HTTP status and allowlisted provider code/type/parameter labels, when present. Raw provider messages, headers, request URLs and evidence are not included. The browser also filters those fields before displaying them. No automatic retry or budget increase is introduced. Capture the new safe code after one explicit rerun before choosing a fix.

## Adaptive provider wait

A subsequent local run returned `provider_timeout`, distinct from the earlier HTTP failure. Adaptive investigations now allow 90 seconds per provider request instead of the shared legacy 30 seconds, with SDK automatic retries disabled in both local and hosted adaptive mode. The timeout was not proven to be the original HTTP failure cause. This is a per-request wait, not a 90-second whole-investigation deadline; tool-turn and dollar limits remain unchanged. Other legacy callers retain their prior defaults. Validate with one explicit live run; do not repeatedly retry failures or increase spending limits to hide a provider problem.

## Empty or interrupted backend responses

The local user log shows the SSE request began with HTTP 200 and later Uvicorn shut down; the backend is currently stopped in that supplied log. A 200 stream response does not establish completion. Empty/non-JSON HTTP responses now show their status without exposing their body or the raw browser JSON exception. Malformed stream frames retain prior activity and cannot produce a final verdict. Restart Uvicorn and keep its terminal open for acceptance testing. The sequence does not prove which event caused the earlier provider HTTP error or timeout.

## Unbilled delivery check

The first completed local case-console run took 117.824 seconds and produced nine
events, four findings, six tools and zero report repairs. The user observed all
tool entries at once, so browser streaming acceptance has **not** passed.

Open Evidence intake → Live connection diagnostics → Test live connection. Three
real server-clock pings are sent one second apart through `/api/stream-check`.
The browser displays server and arrival elapsed times using the same frame reader
as investigations. These are explicitly connection diagnostics, not model/tool
activity. There are no Meta calls. Production access still requires demo credentials.

If arrivals are grouped within 250ms despite server pings spanning two seconds,
the test reports buffering; arrivals spanning at least one second report progressive
delivery. Intermediate timing is inconclusive. This diagnoses the current path,
not every network condition. Try the same unbilled test in a normal Chrome/Edge
tab and compare with VS Code's embedded browser before repeating a billed run.

SSE routes request no-transform and no buffering; those headers are hints, not
guarantees. Production middleware preserves the no-transform header. The Docker
smoke test now measures real ping arrival intervals without using a model. A
passing container test does not establish browser/proxy behavior.
