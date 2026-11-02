# PhantomTrace — submission copy

Prepared November 3, 2026. Match these sections to the platform's actual fields.
This document has not been submitted. Review personal statements and contributors
before publishing. Never put real testing passwords or API keys in this file.

## Project name

PhantomTrace

## Tagline

Follow the evidence. Challenge the story.

## Short description

An evidence-first investigation console for cybersecurity graduates and small IT
teams, powered by Muse Spark and Muse Voice Transcribe.

## Problem and intended user

Recognizing a suspicious log entry is different from knowing what to verify next.
For a new analyst or a small IT team without a dedicated SOC, a useful result
needs more than a confident summary: original sources, competing explanations,
authorization context and a handoff that another person can inspect.

PhantomTrace addresses that investigation workflow. Its motivation comes from
the developer's experience of a gap between university security concepts and
practical investigation. It does not issue certificates or claim to replace
professional training. We have not measured student learning or analyst time savings.

## What it does

PhantomTrace turns submitted security logs into a source-linked case console.
Muse Spark chooses scoped searches, source inspection, supplied change-record
lookups and structured fact checks. A matching record explains only the specific
event it covers; related login or export activity remains separately reviewable.

The console streams actual completed tool executions and displays final findings
after report validation. Analysts can inspect original events on a UTC timeline,
compare model assessments with server-rendered observations, review next checks
and export the investigation trace.

Witness recordings add another source to challenge. Muse Voice Transcribe returns
reviewable text; Muse Spark maps quoted claims to event fields, and the server
compares the mapped values with the logs and supplied record context. Contradictions
remain visible. Approval, identity, intent and the meaning of a model's mapping
still require human judgment.

## Use of Meta models

- `muse-spark-1.3` selects evidence tools, constructs reports and maps witness claims.
- `muse-voice-transcribe-1.0` transcribes uploaded short mono PCM WAV voice notes.
- Server-owned tools are `query_events`, `inspect_events`, `lookup_change` and
  `verify_claims`. They expose evidence operations, not fabricated progress.
- The agent receives tool results and adapts its next request. Structured field
  and timing checks are enforced independently of the model's narrative.

No model training or verified speaker identification is claimed. Muse Spark's
hosted API use does not by itself establish eligibility for an open-weight-model award.

## Technical execution

Python FastAPI backend, React/Vite case console, a bounded model/tool loop,
server-sent tool execution events, source parsing, exact supplied-record matching,
field/timing validation, reviewable voice transcription and JSON export.

A single-origin Docker deployment keeps provider keys in the backend. The public
UI includes a clearly labelled older recorded run. Paid live requests require
private demo credentials and have global request limits plus conservative model
spend reservations. Durable enforcement across restarts requires persistent storage;
the application budget is not an account-wide Meta billing cap. No automatic
remediation or production identity-management integration is claimed.

## Validation and current limits

Automated tests exercise tools, report checks, adversarial fixtures, API access,
stream parsing and the production container without making real model calls.
The developer also completed local and hosted model acceptance checks, including
progressive tool activity, source inspection and witness field contradictions.

One inspected local nine-event export returned four findings and six calls in
117.824 seconds, passed its structured checks and required zero report repairs.
The later hosted run used eight calls; its elapsed time was not supplied. These
are small public synthetic cases, not a throughput guarantee or real-world
accuracy benchmark. Earlier provider failures are retained in the development
record. A voice transcript misheard an identifier, demonstrating the need for review.

An embedded instruction did not override the actor mismatch in the tested witness
example. This is evidence for that example, not comprehensive injection protection.
Next evaluation should use fresh cases and consenting novice users on concrete tasks.

## What was built for the event

The application integration, evidence tools, bounded/adaptive investigation loop,
structured checks, witness workflow, case console, evaluation scripts and deployment
setup are recorded in the project's public Git history. Clearly identify these
event-built contributions in the video. FastAPI, React, Vite, the SDK and Meta models
are third-party components, not original contributions.

## Links

- Product: https://phantomtrace-demo.onrender.com/
- Public code: https://github.com/mirrawrr/PhantomTrace
- Video: add the final accessible video URL in the official form after recording.
- Problem statement: Build for Your World.
- Intended competition track: Indie Developer; confirm the actual platform selection.

## Private testing-field text

Use the organizer-approved private testing field, if available. Enter the real
password there directly; never commit it or publish it in the video/description.

“The public UI and labelled recorded replay need no login. For live tests, open
Evidence intake → Live demo credentials. Username: demo. Use the password supplied
privately in this testing field. Load First shift: maintenance or compromise?, leave
witness testimony empty for the first test, and start Adaptive investigation.
The timeline and actual tool calls appear before final findings. Select a finding
to highlight its events and click an event to inspect the original source. A run
may take around two minutes; timing varies. The optional live connection diagnostic
makes no model calls. If live API allowance is unavailable, use the explicitly
labelled older recording. Never use confidential evidence.”

If still using Render Free, additionally disclose possible cold starts and that
the local budget ledger is ephemeral. Do not claim always-on availability until
the paid service choice and persistence have been verified.

## Judge-facing first test

1. Open the public product link; confirm the page is accessible.
2. Load the mixed synthetic case and run one adaptive investigation with the
   private testing credentials. Avoid unnecessary repeated billed requests.
3. Inspect EVT005 and its CHG-1042 match; review the separately unresolved activity.
4. Export JSON. Optional witness test: deliberately name trainee as EVT005's actor
   and confirm the mapped value differs from source actor admin.

## Confirm before submitting

Final video link, contributor names, personal motivation, hackathon originality
requirements, judge credential delivery method, current hosting configuration,
provider allowance and official deadline. No live submission has been made by
creating this draft. Do not claim a prize ranking, customers or measured impact.
