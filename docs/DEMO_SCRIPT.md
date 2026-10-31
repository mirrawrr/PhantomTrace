# Three-minute PhantomTrace demo

Use the actual app and clearly labelled synthetic evidence. This is a suggested
script, not a claim that the project will win. Rehearse to three minutes. Never
show login passwords, keys, billing details or confidential logs on screen.

## Preparation

- Confirm hosted HTTPS access and privately arrange judge login access.
- Wake the service and run its health/unbilled smoke check before recording.
- Check Meta credits and perform a real synthetic run; preserve failed outputs.
- Open the mixed case, source timeline and actual tool-history views. Loading
  a sample only fills inputs; do not imply it runs an investigation.
- Keep a previously exported real run as an explicitly labelled fallback. If
  editing out wait time, label the edit; do not pretend cached results are fresh.
- Have the public repository and README ready, including evidence limits and
  the retained evaluation failure.

## 0:00-0:20 — A specific user and problem

“When you're a cybersecurity student or a fresh graduate, recognizing a suspicious
log isn't the same as knowing what evidence to investigate next. PhantomTrace helps
a first-time analyst follow leads, challenge an initial suspicion and prepare an
evidence-backed handoff for a small IT team.”

Do not claim every graduate has this problem, that certificates are mandatory,
or that the app replaces professional training. Anchor the motivation in your own
experience. We have not measured improved learning or saved analyst time.

## 0:20-0:40 — Start a real investigation

Load **First shift: maintenance or compromise?**. Show that these are nine
synthetic events and one supplied change record. Start Adaptive investigation.

“A permission change may be legitimate maintenance, while activity from another
account still needs review. The task is to distinguish what the evidence supports
from what we are only assuming.”

## 0:40-1:30 — Explain the mechanism while it works

“Muse Spark chooses scoped evidence searches, source inspection, approval lookup
and factual checks. The tools operate on server-owned evidence. An approval must
match the actor, target, role and time window; it cannot clear an unrelated login.
The server checks structured facts and timing and renders source observations
separately from the model's interpretation.”

The interface shows completed tool history only after the response. Do not pretend
it streams progress or expose private chain-of-thought. If the run finishes sooner,
continue to its results. If it stalls/fails, acknowledge that and use the labelled
previous real run rather than manufacturing an output.

## 1:30-2:15 — Show the useful distinction

- Open EVT005: actor `admin`, target `backup_service`, role `administrator`.
  Show the matching supplied CHG-1042 record and its authenticity caveat.
- Show that the admin failed logins remain separate review findings.
- Open trainee EVT008 and EVT009: unrelated permission activity plus data export.
  Missing approval alone is not proof of an attack; ask what authorization and
  data-sensitivity evidence is needed next.
- Show source event IDs and one actual checked timing relationship.

“The value is not declaring everything an attack. It's separating documented
context, unresolved observations and the next evidence a new analyst needs.”

Do not force a model's output to match this script; demonstrate the actual result
and its limitations. Grant versus revocation is unknown without an operation field.

## 2:15-2:40 — Show the handoff

Open the draft analyst handoff and next checks. Expand one actual tool call and
its short purpose question. Export JSON to show the evidence and execution trace
can be handed to a reviewer. Keep interpretation labelled as requiring review.

## 2:40-3:00 — Evidence, limitations and next step

“In our small public synthetic development set, eight of nine live investigations
completed across the initial run and follow-ups. We retained one unexplained
failure and added safe diagnostics. This isn't a real-world accuracy estimate.
Our next evaluation is with new cases and consenting novice users.”

“PhantomTrace turns a suspicious log into an investigation a new analyst can
inspect and hand off—without treating a confident AI answer as verified evidence.”

## Original contributions and submission

The public Git history records work beginning October 27, 2026. Clearly identify
the event-built contributions: FastAPI/Meta integration, evidence tools, bounded
and adaptive tool loops, claim checks, dashboard, evaluation and deployment setup.
React, Vite, FastAPI, the SDK and other dependencies are third-party components,
not original contributions. Synthetic cases were created for the project.

Submit the public repository, accessible three-minute video and usable product
access using the official platform's current fields. Confirm all contributors
are listed and submission was received. Do not treat a Git push as submission.
The participant guide supplied in chat gives November 4, 9 PM EST, equivalent to
November 5, 10 AM Malaysia time; recheck official announcements before submitting.

For the four rubric categories, show the user problem (impact), actual model/tool
decisions (Meta tooling), checked evidence and failure handling (execution), and
one coherent live workflow (demo). No judge score or top-five outcome is implied.
