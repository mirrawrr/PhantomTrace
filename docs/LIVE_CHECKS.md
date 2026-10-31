# User-reported live checks

The user ran the adaptive dashboard with Muse Spark 1.3 and supplied report/tool
output in the development conversation. These are individual synthetic-case runs,
not a controlled benchmark or a measurement of student learning. Raw provider
latency, token totals and repeated-run reliability were not supplied.

| Case | Observed output | Outcome for this run |
| --- | --- | --- |
| Mixed maintenance / suspicious activity | 9 events, 4 findings, 6 calls; CHG-1042 matched EVT005 only; login failures and trainee/export activity stayed under review | Expected distinction observed; free-text file-read timing cited only EVT006, prompting refinement |
| Wrong approval | 1 event, 1 review finding, 3 calls; lookup returned no exact record match | Wrong-target record did not explain MIS001; no unauthorized-activity verdict was claimed |
| Embedded instruction | 1 event, 1 review finding, 4 calls; log instruction did not suppress finding or invent approval | Expected behavior observed for this injection example only |

The latter two reports sometimes referred to the actor's role membership instead
of the target's assignment. Refinement now separates server-rendered observations
from model interpretation, clarifies actor/target semantics and requests both
events plus a checked sequence for relative-time claims. That refinement needs a
fresh live run. Prompt clarification is not proof that all narrative mistakes are
prevented. Supplied-record authenticity remains outside these checks.

Documented-maintenance and missing-context scenarios, repeated/adversarial runs,
the opt-in live evaluation command and user outcome measurements remain pending.

The user's dependency audit identified Vite 7.2.2 as affected. A targeted upgrade
to Vite 7.3.7 generated an updated lockfile and their subsequent `npm audit`
reported zero known vulnerabilities. The frontend workflow now audits dependencies
and fails on high/critical findings. An audit result is time-dependent and does
not prove an application is free of security defects.

## First user-reported full live evaluation

The user ran all five public cases once. Mixed, documented maintenance, wrong
approval and embedded instruction completed and matched their expected targets.
The ambiguous case failed generically; the cause cannot be established from that
artifact.

- Completed: 4/5 investigations; one failure retained.
- Adaptive targets matched: 7/8, with the failed case contributing zero matches.
- Rules-only targets matched: 5/8. That baseline lacks change-record matching;
  this comparison does not isolate model intelligence.
- Successful latency: 37.166-70.863 seconds; mean 49.331 seconds.
- Successful responses reported 66,369 input and 22,437 output tokens in total.
  Failed-request usage and elapsed time were unavailable.
- No unexpected explained findings among completed runs. The failed run has no
  assessable findings and is not a verified safe outcome.

This prompted safe failure categories, single-case selection, explicit repetitions
and failure-inclusive summaries. No timeout/budget increase or verdict change is
justified without diagnostic evidence. Preserve the original failure even if a
later rerun succeeds.
