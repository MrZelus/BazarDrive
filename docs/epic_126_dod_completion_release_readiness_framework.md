# Epic #126 — Definition of Done Completion & Release-Readiness Framework

This framework converts the current Definition of Done (DoD) into operational execution gates for Epic governance and closure decisions.

## A) DoD gate table

| DoD item (gate) | Meaning in practice | Required evidence | Verification owner | Closure impact if missing |
|---|---|---|---|---|
| 1) All child tasks of Epic are closed. | Every planned subtask/PR mapped to #126 is in final state (`Done/Merged/Closed`) with no unresolved in-scope delivery items. | Updated epic checklist; links to all child issues/PRs; each marked complete with merge SHA/status. | Epic owner + delivery lead (with PM confirmation). | **Hard block:** Epic cannot be closed; release-readiness is incomplete because scope delivery is unproven. |
| 2) No open critical contrast bugs in Epic scope. | There are zero open **critical** readability/contrast defects on `Feed/Rules/Profile` and related scoped surfaces. | Bug board/filter showing no open critical contrast issues; latest regression/contrast run summary with pass evidence. | QA owner + frontend owner (joint sign-off). | **Hard block:** Epic cannot be closed or declared release-ready; unresolved critical UX accessibility risk remains. |
| 3) UI PRs reference Theme Contract and pass visual checklist. | All UI PRs under #126 explicitly reference Theme Contract rules and include completed visual verification (desktop/mobile, Chrome/Edge). | PR descriptions/checklist entries; links to Theme Contract + visual-checklist results; reviewer confirmation in PR. | PR author (self-check) + PR reviewer (enforcement). | **Hard block for closure:** governance/process AC not met; Epic outcomes are not enforceable in future changes. |

## B) Validation order during execution

Recommended gate validation sequence (by earliest reliable verifiability):

1. **Gate 3 (process compliance) — validate continuously from first UI PR.**  
   This gate should start first because it defines how evidence is captured for all later gates.
2. **Gate 2 (critical contrast defects) — validate at each regression cycle and before merge waves.**  
   Becomes reliable after token/state changes are integrated and rerun through regression.
3. **Gate 1 (all child tasks closed) — validate last as final closure gate.**  
   This is the terminal administrative gate that confirms full scope completion.

Practical dependency logic:
- Gate 3 improves traceability needed to prove Gate 2.
- Gate 2 quality status should be stable before declaring Gate 1 complete.
- Gate 1 without Gate 2/3 is formally closed but not release-ready.

## C) Suggested progress-tracking method for #126

Use a **Gate Tracker block** in Epic #126 and update it throughout execution (not only at the end):

1. **Epic-level gate checklist (live):**
   - Gate 1: Child task closure progress (`X/Y done`).
   - Gate 2: Critical contrast bug count (`open critical = N`).
   - Gate 3: UI PR compliance rate (`compliant PRs / total UI PRs`).

2. **Per-PR status comment protocol (mandatory):**
   - `Part of #126` link
   - Theme Contract reference
   - Visual checklist result (desktop/mobile, Chrome/Edge)
   - Any new/remaining critical contrast bugs
   - Next gate impact (`affects Gate 2`, `affects Gate 1`, etc.)

3. **Weekly/iteration gate review snapshot:**
   - Gate state: `Green / Yellow / Red`
   - Blocking reason for each non-green gate
   - Explicit owner + ETA to return to Green

4. **Closure rule:**
   - Epic can move to final closure only when **all three gates are Green** in the latest snapshot.
