# Finish and submit PhantomTrace

Prepared November 3, 2026. Check items only after observing completion.

## Already demonstrated

- [x] Case-console PR #7 merged into main (`e618a07`).
- [x] Developer confirmed hosted tool entries appear during the run and final
  verdicts appear afterward; source inspection and witness checks also worked.
- [x] Local mixed-case JSON inspected: nine events, four findings, six tools,
  117.824 seconds, structured checks passed, zero report repairs.
- [ ] Always-on paid service and persistent ledger verified.
- [ ] Video recorded, edited and tested from its published link.
- [ ] Official form submitted and receipt retained.

## Hosting purchase and setup

For the existing `phantomtrace-demo` web service, review the smallest appropriate
always-on paid **service instance**, not a paid workspace subscription. Published
Starter pricing is $7/month and disk storage is $0.25/GB-month. Starter plus 1 GB
is approximately $7.25/month before tax, bandwidth/build extras and Meta usage.
The dashboard's quote governs. This is recurring hosting, not a one-time purchase.
No billing action has been performed by preparing this checklist.

The owner's Render plan page was read on November 3: the $7/month option is
labelled **0.5c-512mb** (512 MB RAM, 0.5 CPU). It currently says **Payment method
required** and disables upgrades until a card is added. The owner must enter
card details privately through Update Billing; never send them in chat.

Sources: https://render.com/pricing and https://render.com/docs/free .

- [ ] Owner reviews the service-instance quote and chooses whether to purchase it.
- [ ] Confirm the service shows the selected paid instance.
- [ ] Review and add a small persistent disk mounted at `/var/data`; owner confirms
  its actual price before purchase.
- [ ] Add exactly one `DEMO_USAGE_DB=/var/data/phantomtrace-usage.sqlite3` in the
  service environment, save and deploy. Leave keys and passwords private.
- [ ] Keep `DEMO_BUDGET_USD=5`, `DEMO_MAX_REQUESTS=30` and
  `DEMO_HOURLY_REQUESTS=6` unless making a separate budget decision.
- [ ] Verify the deployed page and unbilled connection diagnostic after deployment.
- [ ] In the paid-service Shell, confirm the configured ledger path and its file
  exists after accessing the app. Verify the same file remains after one service
  restart. A harmless marker under `/var/data` can additionally test persistence;
  do not delete/edit allowance rows to perform the test.

Only files under the disk mount persist. Adding a disk without configuring
`DEMO_USAGE_DB` does not persist the allowance ledger. Resolve storage errors
before claiming durable enforcement. Source: https://render.com/docs/disks .

A new ledger path starts a new application allowance; it does not retroactively
include earlier requests or act as an account-wide Meta spending cap. Check
provider usage privately. Never reset a ledger to disguise consumption. No new
model run is required merely to check disk persistence.

## Optional ten-minute user check

Ask a consenting cybersecurity student, graduate or small-team IT practitioner to
use synthetic evidence. Do not publish personal identifiers without permission.

1. Find EVT005's original source and name its actor and target. Does the matching
   supplied record clear the whole investigation?
2. Find the trainee/export sequence and identify the next evidence to collect.
3. Inspect an incorrect witness actor and explain what the field comparison proves.

Record actual completion, confusion and direct feedback with consent. This is
formative usability feedback, not a learning study or representative benchmark.
If nobody is available, leave user testing planned; invent no result.

## Video and judge access

- [ ] Review personal wording in `FINAL_DEMO_SCRIPT.md` for accuracy.
- [ ] Capture real hosted footage; preserve raw recording, exact exports and failures.
- [ ] Label synthetic logs, shortened waits, reused footage and replay.
- [ ] Keep keys, passwords, private dashboards and notifications out of capture.
- [ ] Show streamed tools, scoped record match, original source, reviewable voice
  transcription and a deliberately edited witness/instruction example.
- [ ] Trim to three minutes; confirm voice and evidence IDs are clear at 720p.
- [ ] Upload the final video and open its URL in a signed-out/private window.
- [ ] Confirm the organizer-approved private channel/field for testing credentials.
  The prepared Discord question has not been sent by the agent.
- [ ] Provide only the demo password there; never give judges the Meta API key.

The inspected local 117.824-second run is not a guarantee for today's recording.
Use only metrics from the exact footage/export when quoting a measured result.

## Submit

- [ ] Review `SUBMISSION_DRAFT.md`, confirm platform-specific fields, choose the
  actual Indie Developer track and Build for Your World problem statement.
- [ ] Confirm contributors, original event-built work, dependency credits and
  public repository/video accessibility.
- [ ] Verify the current official deadline and any updates in the logged-in platform.
- [ ] Owner reviews the complete form and terms, submits, and saves its receipt,
  timestamp, public code revision and exact video URL.
- [ ] After judging, review recurring hosting/disk charges deliberately; preserve
  evidence before making any later service or storage change.

The participant guide supplied in chat states November 4 at 9 PM EST, equivalent
to **November 5 at 10:00 AM Malaysia time**. At November 3, 3:54 AM MYT, that was
about 54 hours away. The public details page did not expose its loaded text to
the web tool on November 3; reconfirm in the platform/announcements. Aim to finish
well before the last hour. Official page:
https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details .

A merged PR, live website or uploaded video is not a completed submission.
This document creates no billing action, monitoring job or reminder.
