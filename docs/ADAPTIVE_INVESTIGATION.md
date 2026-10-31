# Adaptive investigation: first analyst workflow

PhantomTrace helps a fresh graduate or small IT team follow leads, examine
competing explanations and prepare a handoff. It does not replace professional
training, certifications or senior review.

## Run

Use the existing two-terminal setup. Restart FastAPI and Vite on this branch.
The dashboard defaults to **Adaptive investigation**. Select **First shift:
maintenance or compromise?**, click **Load sample**, then **Start investigation**.
Loading a case only fills the inputs; model results are never prewritten.
Optional change records are editable JSON. The original fixed workflow remains
selectable and available at `POST /api/investigate/agent`.

The new endpoint is `POST /api/investigate/adaptive`, accepting
`{"logs":"...","changes":[]}`. A change record contains `change_id`, `actor`,
`target`, `role`, `starts_at`, `ends_at`, and `status` (`approved` or `revoked`).
Dates require timezones. Duplicate change IDs and invalid windows are rejected.

## Investigation tools

The model starts with event-type counts and deterministic triage leads. It chooses
tools and filters; there is no mandatory tool order.

| Tool | Purpose |
| --- | --- |
| `query_events` | Search by user, IP, event type or inclusive time window |
| `inspect_events` | Read original entries by ID |
| `lookup_change` | Check an exact actor/target/role/time approval match |
| `verify_claims` | Check structured field values and timing relationships |

Query filters combine with AND. Bounded pages disclose omitted matches through
`truncated` and `next_offset`. Tools cannot replace evidence. Actual calls include
a short analyst-facing question explaining their purpose, not private reasoning.
Tool errors are visible and can be corrected. Limits are ten model turns, four
calls per turn and 24 calls total. Invalid final reports get a repair request
within the same budget. Provider timeout/retries apply per request; there is no
overall deadline or streaming progress. Browser cancellation may not stop Meta.

## Verification boundaries

Every cited event must have been inspected and needs at least one checked fact.
Supported fields are event type, user, IP, target, role and timestamp. Optional
sequence checks validate strict ordering and maximum elapsed time. Timestamps are
ordered by instant across timezones. Facts are rechecked on final reports even
when `verify_claims` was not called. Triage leads cannot be silently omitted.

An `explained_by_record` finding must cite exactly one permission event plus a
record actually returned by `lookup_change`. It requires approved status, exact
actor, target and role, and an inclusive time window. This cannot clear associated
logins or an entire incident. No match does not prove unauthorized activity.

**The server does not authenticate supplied records or verify free-text narrative,
intent, causation or complete incident coverage.** One correct event-type fact
does not validate every sentence in a finding. Human review remains necessary.
The dashboard states these limits and shows alternate explanations, next checks,
fact details and a draft analyst handoff.

Source-backed observations are rendered by the server from original cited events,
not copied from model prose. Permission records label `user` as actor and `target`
as the affected subject; a role field alone does not prove grant versus revocation.
Only submitted, successfully checked sequences generate relative-time observations
with both event IDs. Free-text model assessment is shown separately and may still
contain unsupported claims. Executive summary, alternatives, next checks and
handoff remain model-generated and require review. Empty sequences mean no
cross-event timing relationship was submitted for that finding.

## Evaluation

Five public synthetic fixtures in `frontend/src/scenarios.json` cover mixed
activity, documented maintenance, missing context, wrong approval and instructions
hidden in evidence. Expected labels are hand-authored regression targets and are
not sent to Meta. These are not authenticated incident truth or a held-out set.

From the repository root, using the backend environment:

```powershell
.\backend\.venv\Scripts\python.exe scripts/evaluate_adaptive.py
```

Offline mode measures the rules-only baseline and marks adaptive results **NOT
RUN**. Add `--live` to measure actual Muse Spark behavior using your local key.
This sends synthetic evidence to Meta and consumes API credits. Output includes
target dispositions/coverage, unexpected explained findings, tool paths, latency
and provider-reported token totals. Costs are not estimated; raw provider errors
are not included in results.

The rules-only baseline lacks change-record matching. This compares capability
coverage, not isolated model quality. Five public cases do not establish real-world
accuracy, generalization or learning effectiveness. Preserve failures and do not
advertise improvements before measured live runs exist. A separate held-out set
and consenting novice-user study are future work.

Mocked tests establish tool/validation mechanics, not live-model decision quality
or prompt-injection resistance. Live adversarial evaluation remains necessary.

## Acceptance before merging

1. Run the mixed case. Inspect admin and trainee activity, including EVT009's
   export, which deterministic triage does not flag.
2. Check whether the matching record explains EVT005 only. Login failures and
   trainee activity must not be cleared by CHG-1042.
3. Open evidence IDs and compare narrative claims with source entries.
4. Inspect tool questions/results and compare actual paths across cases.
5. Run documented maintenance and wrong-approval cases. Wrong targets, revoked
   records and out-of-window records must not qualify as exact matches.
6. Run the adversarial case. The log instruction must not remove the lead or
   create a fake approval. Inspect free text as well as deterministic checks.
7. Review the handoff, export JSON, and run the live evaluation.

No live-model benchmark or learning-outcome improvement is claimed by this change.

### Diagnose one case

```powershell
.\backend\.venv\Scripts\python.exe scripts/evaluate_adaptive.py --live --case ambiguous
```

Use a different output file from the original evaluation. Add `--repeat 3` only
to intentionally make three additional attempts and incur their API cost. All
attempts stay in the output; no failed run is silently replaced by a success.
Offline selection is also supported without `--live`.

Safe failure categories distinguish provider timeout, connection, authentication,
rate limit, HTTP error, incomplete/model-limited output and turn/tool budgets.
Agent diagnostics include elapsed time, turns, allowlisted tool names, tool-error
counts, report-rejection categories and schema field paths/types without input
values (unknown field names are replaced). Raw provider messages, headers, URLs,
credentials, evidence and raw reports are excluded. Unknown errors remain generic.
The HTTP endpoint still returns a sanitized error. Incomplete model output is not
accepted as a report.

Summary denominators include failed cases with zero matched targets. These are
synthetic target matches, not an accuracy estimate. Successful metrics include
model turns and report repairs. Failure diagnostics omit token totals because
provider usage may be unavailable for a failed request.
