# Ready-to-paste GitHub Milestone Descriptions

## Purpose

Этот документ содержит **готовые описания для GitHub Milestones** проекта **BazarDrive**.

Их можно использовать почти без редактирования:
- открыть GitHub;
- создать milestone;
- вставить соответствующий title + description;
- назначить issues по таблице из `docs/github_milestones.md`.

Связанные документы:
- `docs/roadmap.md`
- `docs/github_milestones.md`

---

## Milestone 1

### Title

`Wave A — Compliance Core & Release Readiness`

### Description

Build the technical core for driver compliance, eligibility checks, and release-ready contracts/tests.

### Scope
- driver compliance migrations and entities
- ORM models and repository layer
- compliance service and eligibility evaluation
- API endpoints for compliance state
- integration of compliance guard into key order-flow entry points
- regression coverage for compliance module
- release hygiene: contracts, tests, OpenAPI sync, release checklist

### Included issues
- #175
- #204
- #266
- #278
- #279
- #280
- #281
- #282
- #283
- #285

### Exit criteria
- migrations apply cleanly
- compliance entities are accessible through repository layer
- compliance service returns structured eligibility state and blocking reasons
- API exposes stable compliance endpoints
- key guarded actions block invalid drivers server-side
- tests and release-readiness docs are aligned with implementation

### Notes
This milestone comes first because the rest of the driver/taxi workflow depends on a real compliance core rather than placeholder UX.

---

## Milestone 2

### Title

`Wave B — Driver Readiness UX`

### Description

Deliver the driver-facing readiness experience: legal profile, vehicle, documents, waybill, and summary UX required for operational taxi eligibility.

### Scope
- legal identity and qualification fields
- entrepreneur / legal status section
- vehicle profile and taxi equipment state
- driver documents UI and statuses
- waybill open/close flow
- readiness summary card with actionable next steps

### Included issues
- #267
- #268
- #269
- #270
- #272
- #273

### Exit criteria
- driver can fill all required legal and qualification fields
- vehicle profile supports required taxi-related attributes
- document list shows correct statuses and required actions
- waybill state participates in readiness / eligibility logic
- summary card clearly explains whether the driver can work and what must be done next

### Notes
This milestone turns driver profile UX into a real operational cockpit instead of a passive profile form.

---

## Milestone 3

### Title

`Wave C — Compliance Automation & Moderation`

### Description

Automate document lifecycle, reminders, moderation, and compliance support flows so the platform can keep driver readiness current without relying on manual upkeep.

### Scope
- order journal compliance storage
- expiry reminders and action prompts
- moderator review decisions for driver documents
- background job for expired / expiring-soon document states

### Included issues
- #274
- #275
- #276
- #284

### Exit criteria
- documents move into `expired` / `expiring_soon` automatically when needed
- reminders are useful and non-spammy
- moderator can approve/reject documents and leave rejection reasons
- order journal stores required compliance-related snapshots
- compliance state becomes auditable and ready for export / review

### Notes
This milestone is where compliance stops being a static data layer and becomes a living system.

---

## Milestone 4

### Title

`Wave D — Feed, Trust & Role UX Hardening`

### Description

Harden the publication/feed platform: role-based profile UX, trust/document consistency, moderation rules, ownership checks, and stable interaction flows.

### Scope
- role matrix enforcement for profile tabs
- documents and trust layer consistency
- feed reactions and comments hardening
- moderation and object-level authorization
- delete/edit ownership checks
- media/photo support follow-through where needed

### Included issues
- #110
- #171
- #172
- #173
- #174
- #177
- #182
- #184

### Exit criteria
- role matrix is enforced consistently in UI behavior
- trust/document states do not drift away from role logic
- object-level authorization works predictably
- delete/edit ownership flows are covered and stable
- feed interactions survive reload, errors, and regression scenarios
- docs, tests, and product behavior stay in sync

### Notes
This milestone consolidates the publication/feed part of BazarDrive after the core driver/compliance layers are stabilized.

---

## Compact versions

Эти версии можно использовать, если нужен короткий description в GitHub UI.

### Wave A — Compliance Core & Release Readiness
Build the driver compliance backend core, eligibility checks, guarded order-flow entry points, and release-ready contracts/tests.

### Wave B — Driver Readiness UX
Deliver the driver-facing readiness experience: legal profile, vehicle, documents, waybill, and summary UX.

### Wave C — Compliance Automation & Moderation
Automate document lifecycle, reminders, moderation, and order-journal compliance support flows.

### Wave D — Feed, Trust & Role UX Hardening
Harden the publication/feed platform: role UX, trust/document consistency, moderation rules, ownership checks, and stable interactions.

---

## Suggested usage

### Option 1
Use the full versions above for milestone descriptions in GitHub.

### Option 2
Use the compact versions in the GitHub UI and keep detailed scope only in repo docs.

### Option 3
Use full descriptions at creation time, then shorten them later if milestone pages become cluttered.

---

## Note

Если later появятся новые roadmap-waves, лучше добавлять их сюда в том же формате:
- title
- description
- scope
- included issues
- exit criteria
- short version
