# Ready-to-paste GitHub Cleanup Comments and Epic Update Templates

## Purpose

Этот документ содержит **готовые тексты для cleanup backlog** в GitHub по проекту **BazarDrive**.

Он нужен для двух задач:
- быстро оставлять понятные комментарии при закрытии duplicate / follow-up issues;
- быстро обновлять описания epic-issues без ручного сочинения каждый раз.

Связанные документы:
- `docs/github_cleanup_plan.md`
- `docs/github_issue_assignment_plan.md`
- `docs/github_milestones.md`
- `docs/roadmap.md`

---

## 1. Duplicate issue comments

### Template A — close as duplicate of another issue

```md
Closing as duplicate of #<PRIMARY_ISSUE>.

To keep implementation tracking, docs updates, and regression discussion in one place, we are consolidating this work under #<PRIMARY_ISSUE>.

If there is any unique context in this thread that still matters, it should be copied into #<PRIMARY_ISSUE> before final closure.
```

---

### Template B — short duplicate closure

```md
Closing as duplicate of #<PRIMARY_ISSUE> to avoid split tracking.
Primary implementation discussion will continue there.
```

---

### Ready text for #277 -> #278

```md
Closing as duplicate of #278.

Both issues track the same driver compliance migration work, and keeping them both open would split implementation tracking unnecessarily.

Primary migration discussion should continue in #278.
```

---

### Ready text for #182 -> #184

```md
Closing in favor of #184 as the primary issue for guest feed photo upload support.

The goal, scope, and implementation path overlap heavily, so keeping one primary issue will make tracking cleaner and reduce split discussion across docs, UI behavior, and regression coverage.

Any unique notes from this thread can be copied into #184 if they still matter.
```

---

## 2. Follow-up / hardening reframing comments

### Template C — keep as follow-up hardening issue

```md
Reframing this issue as a follow-up hardening task after the primary implementation in #<PRIMARY_ISSUE>.

The main feature scope should stay consolidated in #<PRIMARY_ISSUE>, while this issue remains focused on post-MVP polish such as UX, validation, stability, or regression hardening.
```

---

### Template D — narrow scope after cleanup

```md
Narrowing the scope of this issue during backlog cleanup.

This issue will remain open, but only as a follow-up task for:
- UX polish
- validation refinements
- error handling improvements
- regression hardening

Primary implementation scope is tracked in #<PRIMARY_ISSUE>.
```

---

### Ready text for keeping #182 as follow-up to #184

```md
Reframing this issue as a follow-up hardening task after the primary implementation in #184.

The main guest feed photo upload scope should stay consolidated in #184. This issue can remain open only for post-MVP polish such as:
- upload UX refinements
- validation edge cases
- error handling polish
- regression hardening
```

---

## 3. Epic cleanup comments

### Template E — epic indexing / child issue structure update

```md
Updating this epic during backlog cleanup so it works as a real umbrella issue rather than a broad standalone ticket.

Suggested child structure:

### Backend / technical foundation
- #...
- #...

### Driver-facing / user-facing scope
- #...
- #...

### Automation / moderation / follow-up
- #...
- #...

This should make milestone assignment and implementation order clearer.
```

---

### Template F — tighten epic boundaries

```md
Clarifying scope boundaries for this epic during cleanup.

### In scope for the current roadmap phase
- ...
- ...

### Out of scope for now
- ...
- ...

This is meant to keep the epic actionable and prevent it from turning into an open-ended meta-container.
```

---

## 4. Ready epic update blocks

### Ready block for #266

```md
Updating this epic during backlog cleanup so it functions as a clear umbrella for the driver compliance roadmap.

### Backend foundation
- #278 — migrations
- #279 — ORM models
- #280 — repository layer
- #281 — compliance service
- #282 — API endpoints
- #285 — tests

### Driver-facing readiness
- #267 — legal identity and qualification
- #268 — entrepreneur / legal status
- #269 — vehicle profile
- #270 — documents
- #272 — waybill flow
- #273 — readiness summary

### Automation and moderation
- #274 — order journal
- #275 — reminders
- #276 — admin moderation
- #284 — expiry background job

### Order-flow integration
- #283 — compliance guard in order flow

This grouping should make implementation order and milestone mapping much easier to follow.
```

---

### Ready block for #173

```md
During cleanup, this epic should be treated as a product umbrella for feed interaction hardening, not as a single implementation ticket.

Recommended child issue directions:
- feed reactions: server-side state and `my_reaction` consistency
- feed comments: ownership, edit, delete, and error handling
- feed list UX hardening: pagination, infinite scroll, search, filter stability
- feed interaction regression coverage

This will make the epic easier to execute and reduce ambiguity around what “done” means.
```

---

### Ready block for #174

```md
During cleanup, this epic should stay focused on moderation, safety, and authorization rules rather than absorbing all feed-related work.

Recommended concrete child issue directions:
- object-level authorization for posts
- object-level authorization for comments
- moderator override normalization
- prod write-auth and CORS hardening
- negative test coverage for ownership and forbidden cases

#110 can remain one of the concrete implementation issues under this epic.
```

---

### Ready block for #175

```md
Clarifying scope boundaries for this epic during cleanup so it does not become an open-ended container for all platform improvements.

### In scope for the current roadmap phase
- OpenAPI sync for active modules
- regression coverage for active milestone flows
- release readiness checklist tied to active waves
- docs/tests/contract alignment for in-flight work

### Out of scope for now
- full CI/CD redesign
- mass test refactor unrelated to active roadmap waves
- broad platform engineering work without direct roadmap linkage

This keeps the epic useful and milestone-friendly.
```

---

## 5. Title update suggestions

Эти тексты можно использовать как comment перед rename или как note в cleanup discussion.

### For #171

```md
Optional cleanup suggestion: rename this epic to better reflect its actual scope.

Current:
- Epic: Publication Profile & Role UX

Possible rename:
- Epic: Publication Profile, Role Matrix & Navigation UX

Reason:
The actual scope strongly includes role-based tab access and navigation guard behavior, so adding that to the title makes the epic more self-explanatory.
```

---

### For #172

```md
Optional cleanup suggestion: rename this epic to better reflect its real UI/product behavior.

Current:
- Epic: Documents & Trust Layer

Possible rename:
- Epic: Documents, Trust States & Verification UX

Reason:
The current work is not only about abstract trust concepts, but about visible trust states and verification behavior in the UI.
```

---

## 6. Status / triage comments

### Template G — mark as follow-up after main roadmap wave

```md
Keeping this issue open as a follow-up item after the primary roadmap wave is completed.

It is still useful, but it should not compete with the current milestone’s core foundation work.
```

---

### Template H — mark as milestone-specific focus

```md
Assigning this issue to the current milestone because its main value is directly tied to the active roadmap wave.

Even if it touches other areas, its primary outcome belongs here.
```

---

### Ready text for #204

```md
Keeping this issue as a small hardening follow-up.

It is useful because verification/trust mapping should stay consistent while the broader compliance and profile layers evolve, but it should remain intentionally narrow and not expand into a new product scope.
```

---

## 7. Suggested epic description snippets

Эти фрагменты можно прямо вставлять в epic descriptions.

### Snippet — Implementation order

```md
## Implementation order

1. technical foundation
2. user-facing readiness / UX layer
3. automation / moderation layer
4. hardening and regression coverage
```

---

### Snippet — Milestone alignment

```md
## Milestone alignment

Primary milestone:
- Wave <X>

This epic may touch other layers, but its main outcome belongs to this wave.
```

---

### Snippet — Child issue index

```md
## Child issue index

- #...
- #...
- #...
```

---

## 8. Suggested usage order

### Step 1
Use duplicate comments first:
- #277 -> #278
- #182 -> #184 or reframe #182 as follow-up

### Step 2
Then update epic issues using the ready blocks:
- #266
- #173
- #174
- #175

### Step 3
Then optionally add cleanup notes for title refinements:
- #171
- #172

### Step 4
Only after cleanup comments are in place, finish milestone + labels assignment.

---

## Note

Хороший cleanup comment должен быть коротким, ясным и объяснять **почему задача меняет статус**. Не нужно превращать комментарии в роман. Они должны работать как дорожные знаки: один взгляд, и уже понятно, куда дальше двигаться.
