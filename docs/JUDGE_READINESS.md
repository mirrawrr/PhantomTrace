# Judge access and witness evidence

This upgrade is a candidate for live acceptance testing, not a tested winning claim.

## Access

Set `DEMO_PUBLIC_UI=true` in the Render service environment and redeploy the merged
commit. `/` and built `/assets/` then open without a browser password box. All API
routes and docs remain private; enter `demo` and the private `DEMO_PASSWORD` in
the dashboard's Live demo credentials section. Keep these in the submission's
private testing field if organizers permit. Never put the password in GitHub,
a public video, sample logs or URL. The form holds it only in page memory.

Replay a recorded run is immediately available once the page loads. It is the
real five-event export previously supplied by the developer, not the newer
adaptive case. Its missing recording timestamp, older pipeline and replay status
are visible; exports retain provenance. It makes no model call. It does not
remove a Free service's initial cold start.

## Always-on judging and durable usage limits

Render Free sleeps after 15 idle minutes and can take about a minute to wake:
https://render.com/docs/free

For November 5–9 judging, choose an always-on paid **service instance**, not merely
a paid workspace plan. Billing changes require the owner's choice. Do not rely on
periodic pings as a guarantee. Add a persistent disk mounted at `/var/data` and set
`DEMO_USAGE_DB=/var/data/phantomtrace-usage.sqlite3`. One service instance/disk is
supported. Without persistent storage, the SQLite ledger resets on restart or
redeploy. Never advertise a durable spending cap with an ephemeral ledger.

Hosted startup enables the model budget. Defaults: `DEMO_BUDGET_USD=5`,
`DEMO_MAX_REQUESTS=30`, `DEMO_HOURLY_REQUESTS=6`. These are global shared limits,
not per-IP limits that a proxy header can bypass. Auth runs before the allowance
middleware. Failed/invalid authorized attempts count toward request limits.

Before each Spark call, SQLite atomically reserves $1.40, covering the full
1,048,576-token context at uncached input pricing plus the bounded 6,500 output
tokens. Actual reported input/output usage reconciles down, with no cache
discount assumed. Failed/unknown-usage calls retain the full reservation; no SDK
retry is enabled. Voice reserves $0.003 per <=60-second note. Caps are conservative:
the last $1.40 must remain available to start a Spark call. They do not represent
the provider invoice or other apps using the same key. Pricing assumptions checked
November 1: https://dev.meta.ai/docs/pricing-rate-limits . Recheck before changing
model/pricing; only bounded `muse-spark-1.3` and local function tools are supported.
The old unbounded `/api/investigate` endpoint is unavailable under this hosted
budget; dashboard adaptive and fixed-agent paths have bounded outputs.

Keep a separate provider-account budget/alert as an additional control. A spend
notification alone is not a hard cap. No account billing setting was changed.

## Voice testimony acceptance

Official contract: https://dev.meta.ai/docs/speech-to-text . Recorded-file upload
uses `/v1/asr/transcribe`, `muse-voice-transcribe-1.0`, multipart request/audio
parts and server-only authentication. The dashboard accepts <=60 seconds of mono
16-bit PCM WAV at 16/24 kHz. MP3/M4A/Opus require conversion first; there is no
browser microphone capture in this version. No audio is saved by PhantomTrace.

1. Use synthetic speech you have permission to send to Meta. Example: "EVT005
   records admin changing backup_service to administrator. This was approved."
2. Upload the note and inspect/correct the transcript before starting. Typed text
   works as a fallback, explicitly without a claim of voice-model execution.
3. Spark extracts quoted claims; the existing workspace fact verifier compares
   mapped event fields and `lookup_change` checks supplied record context.
4. A field match is not proof of a witness's meaning, identity or intent. Semantic
   mapping is model-generated and remains reviewable. Business justification and
   broad approval claims remain not-checkable. No approval record is fabricated.
5. Try a statement naming the wrong actor; the mapped source value must differ.
   Try instruction-like speech; it must remain data, with no changed log verdict.

The voice route has contract tests using a fake provider. A real account-enabled
transcription plus claim check must pass before it is presented as working live.
Claim checks run separately after the log report, so report tool count/latency/token
metrics exclude the additional extraction call and transcription. If that optional
check fails, the log report remains available and testimony is marked unverified.

## Demo and impact

Lead with the user's real university-to-first-job gap. Do not invent employment,
industry adoption, certificate requirements or learning outcomes. Position this
as open-source/self-hostable investigation support for a small IT team without a
dedicated SOC; it does not issue certifications or replace training.

Headline moment: show the **existing permission-change injection case**, its
instruction-like note, ignored instruction and retained review finding. That case
does not contain a data export. Do not say a server proves an arbitrary narrative
or detects every prompt injection. An export injection case requires its own new
fixture, checks and actual measured run before making that demo claim.

Use measured figures: the public synthetic mixed case previously matched 4/4
expected target instances in 70.863 seconds. This is not accuracy or a realistic
2,000-line throughput benchmark. The UI currently caps logs at 20,000 characters,
so do not claim 2,000 lines reduced in under a minute. Obtain a representative
permitted sample and measure before adding such a number. Retain failures in all
evaluation totals. Collect an actual first-time analyst's task feedback next.

## Organizer question (prepared, not sent)

“Our public PhantomTrace UI includes an instant, clearly labelled recorded replay.
Live AI investigations require shared demo credentials to control API spend. May
we provide those credentials in the private submission testing field, and will
all judges have access to it? Is there a preferred access method or availability
window for November 5–9?”

Send in Discord #questions today. No Discord message has been sent by this change.

## Witness-check diagnostics and separate retry

The first user live attempt completed the log investigation but returned the
generic witness-check failure. Its original cause is unknown. Do not describe
that run as successful end-to-end voice verification.

Witness failures now report allowlisted categories such as `model_output_limit`,
`model_schema_invalid`, `quote_source_mismatch`, provider timeout or budget
unavailable. No raw provider response, key or testimony is included in error
messages. Extraction has a 4,000-token output allowance; nullable unmapped claim
fields may be omitted. Exact quotation checking remains enforced. These changes
do not establish which failure occurred in the first run.

Use **Check witness only** under the statement box to submit the current logs,
change records and statement without repeating the full investigation. This is
one additional paid Spark request and no new transcription. Its separate panel
identifies current submitted inputs; it does not modify the log report. The API
is `/api/investigate/testimony`, protected by the same authentication, request
limits and dollar reservations as other live investigation endpoints. No automatic
retry occurs. Retain the safe failure code if it fails again.
