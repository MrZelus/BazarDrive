# GitHub Backlog Cleanup Plan for BazarDrive

## Purpose

Этот документ описывает **боевой cleanup plan для GitHub backlog** проекта **BazarDrive**.

Цель cleanup:
- убрать дубли и пересечения;
- сделать backlog легче для навигации;
- привести epics, milestones и implementation issues к одной логике;
- уменьшить шум перед активной работой по roadmap waves.

Связанные документы:
- `docs/roadmap.md`
- `docs/github_milestones.md`
- `docs/github_milestone_descriptions.md`
- `docs/github_labels.md`
- `docs/github_issue_assignment_plan.md`

---

## Cleanup principles

### Principle 1 — Keep the roadmap spine visible

После cleanup в backlog должны чётко читаться четыре большие волны:
- Wave A — Compliance Core & Release Readiness
- Wave B — Driver Readiness UX
- Wave C — Compliance Automation & Moderation
- Wave D — Feed, Trust & Role UX Hardening

Если issue не помогает понять, в какой волне она живёт, её нужно:
- переименовать;
- промаркировать;
- или привязать к epic / milestone яснее.

---

### Principle 2 — Prefer one primary issue over overlapping twins

Если две задачи описывают почти один и тот же результат:
- выбрать **одну primary issue**;
- вторую закрыть как duplicate или оставить как узкий follow-up.

Иначе backlog начинает дышать двойным эхом.

---

### Principle 3 — Epics should not behave like implementation tickets

Epic должен:
- задавать цель;
- задавать scope;
- ссылаться на подзадачи;
- не подменять собой техническую реализацию.

Если epic начинает жить как обычная фича-задача, стоит:
- оставить epic как umbrella;
- вынести конкретную реализацию в sub-issues.

---

### Principle 4 — Cross-cutting issues need explicit boundaries

Некоторые задачи пересекают несколько волн, например quality или trust hardening. Для них нужно явно указать:
- почему они назначены именно в этот milestone;
- что считается завершением;
- не являются ли они бесконечными “meta-tasks”.

---

## Recommended cleanup actions

## 1. Consolidate duplicate / overlapping issues

### Pair: #182 and #184

**Issues:**
- #182 — Добавить поддержку загрузки фото в гостевой ленте
- #184 — Добавить поддержку загрузки фото в гостевой ленте

### Assessment
Обе задачи покрывают почти один и тот же пользовательский результат:
- UI выбора изображения;
- отправка изображения в `POST /api/feed/posts`;
- отображение фото в ленте;
- обновление документации и тестов.

#184 выглядит более развёрнутой и более аккуратно связанной с roadmap / Linear context, тогда как #182 тоже подробна, но выглядит как соседняя версия того же направления.

### Recommendation
**Primary issue:** оставить **#184** как основную задачу.

**For #182:**
выбрать один из двух вариантов:

#### Option A — Close as duplicate
Использовать, если подтверждено, что в #184 уже есть весь нужный scope.

Suggested comment idea:
> Closing in favor of #184 as the primary issue for guest feed photo upload support. Keeping implementation, docs, and regression discussion in one place to avoid split tracking.

#### Option B — Reframe as hardening follow-up
Использовать, если хочется сохранить вторую задачу для post-MVP polish.

Suggested new title for #182:
`Feed photo upload hardening: UX, validation, and regression follow-up`

Suggested labels:
- `type:hardening`
- `status:follow-up`
- `priority:p3`

### Preferred path
**Рекомендую Option A**, если нет уже начатой работы отдельно по #182. Один primary issue здесь будет чище.

---

## 2. Resolve likely accidental duplicates in compliance migration layer

### Pair: #277 and #278

**Issues:**
- #277 — Tech: Alembic migrations for driver compliance module
- #278 — Tech: Alembic migrations for driver compliance module

### Assessment
Судя по названию и описанию, это практически дубль. В roadmap и assignment plan уже использовался #278 как основной migration issue.

### Recommendation
**Primary issue:** оставить **#278**.

**For #277:**
- закрыть как duplicate of #278;
- если в #277 есть отдельные комментарии/контекст, перенести нужное в #278 перед закрытием.

Suggested comment idea:
> Closing as duplicate of #278 to keep driver compliance migration tracking in a single issue.

### Preferred path
**Закрыть #277 как duplicate**.

---

## 3. Tighten epic naming where needed

Некоторые эпики уже хорошие и читаемые. Но cleanup выигрывает, если названия сразу говорят, о каком слое идёт речь.

### Keep as-is
Эти названия уже достаточно сильные:
- #266 — Epic: Driver legal profile, documents, and taxi compliance
- #173 — Epic: Feed Engagement & Interaction
- #174 — Epic: Moderation, Safety & Authorization
- #175 — Epic: Quality, Contracts & Release Readiness

### Consider small title tightening

#### #171 current
`Epic: Publication Profile & Role UX`

Possible rename:
`Epic: Publication Profile, Role Matrix & Navigation UX`

Why:
слово navigation там реально важно и лучше отражает фактический scope.

#### #172 current
`Epic: Documents & Trust Layer`

Possible rename:
`Epic: Documents, Trust States & Verification UX`

Why:
так яснее, что речь не про абстрактный trust-platform слой, а про конкретные trust states / verification behavior в UI.

### Recommendation
Это **не обязательно**, но полезно, если хочется сделать epic list более самодокументируемым.

---

## 4. Convert some broad issues into explicit parent/child structure

### Candidate: #266

#266 уже хороший umbrella epic, но для GitHub cleanup полезно закрепить в описании явный блок:
- `Implementation order`
- `Related tech issues`
- `UX / feature issues`

### Recommendation
В описание #266 стоит явно добавить структуру:

#### Backend foundation
- #278
- #279
- #280
- #281
- #282
- #285

#### Driver-facing readiness
- #267
- #268
- #269
- #270
- #272
- #273

#### Automation and moderation
- #274
- #275
- #276
- #284

#### Order-flow integration
- #283

### Why
Так epic перестанет быть просто большой постановкой и станет реальным index-node.

---

### Candidate: #173

#173 сейчас задаёт направление feed interaction, но cleanup выиграет, если рядом будут явные implementation tickets на:
- reactions consistency;
- comment ownership / edit / delete;
- feed interaction error UX;
- pagination/infinite scroll hardening.

### Recommendation
Если таких sub-issues ещё нет, **создать под #173 отдельные implementation issues** вместо того, чтобы держать всё в одном epic как туманную тучу.

Suggested child issue directions:
- Feed reactions: server-side state and `my_reaction` consistency
- Feed comments: ownership, edit, delete, and error handling
- Feed list UX hardening: pagination/infinite scroll/search/filter stability
- Feed interaction regression pack

---

### Candidate: #174

#174 уже сильный epic, но ему не помешают более явные подзадачи:
- object-level auth for posts
- object-level auth for comments
- moderator override normalization
- prod write-auth / CORS hardening

### Recommendation
Держать #110 как один из concrete implementation tickets под #174 и при необходимости добавить ещё 2-3 узкие задачи вместо расплывчатого общего coverage.

---

## 5. Mark cross-cutting epics so they do not become infinite sinks

### Issue #175

Это полезный epic, но у него есть риск стать бесконечной “коробкой для всего полезного”.

### Recommendation
Добавить в описание #175 явный блок:

#### In scope for current roadmap phase
- OpenAPI sync for active modules
- regression pack for current milestone flows
- release checklist for active waves

#### Out of scope for now
- full CI/CD redesign
- mass refactor of all tests
- broad platform engineering work unrelated to active milestones

### Why
Чтобы #175 не превращался в чёрную дыру, куда падают все “надо бы улучшить”.

---

### Issue #204

#204 небольшой и полезный hardening issue. Его не нужно расширять.

### Recommendation
Оставить как есть, но пометить:
- `type:hardening`
- `status:follow-up`

Это снизит риск случайного раздувания scope.

---

## 6. Reclassify a few issues by intent if needed

### #273
Сейчас это feature, но по смыслу это ещё и очень сильный UX/cockpit issue.

### Recommendation
Добавить к нему:
- `type:ux`

Не вместо `type:feature`, а как дополнительный сигнал в triage, если в репозитории допустимо два type-like label. Если хочешь держать один type-label на issue, оставить `type:feature`, но упомянуть в описании, что это UX-facing summary layer.

---

### #110
Технически это API/authorization feature, но по operational смыслу это hardening moderation/auth слоя.

### Recommendation
Можно оставить `type:feature`, но при желании переосмыслить как:
- `type:hardening`

Если задача воспринимается как добивка уже существующего feed API.

---

## 7. Add explicit duplicate / follow-up hygiene comments

Cleanup полезнее, если после него остаётся не молчание, а понятный след в backlog.

### For duplicates
Использовать короткие прозрачные комментарии:
- closed as duplicate of #...
- keeping active implementation in #...
- consolidating discussion to avoid split tracking

### For follow-ups
Использовать формулировки:
- narrowed to hardening scope
- keeping as post-MVP follow-up
- reduced to regression / UX polish work after primary implementation issue

---

## 8. Suggested concrete action list

### Action A — Close duplicates
- Close **#277** as duplicate of **#278**
- Review **#182** vs **#184** and either:
  - close **#182** as duplicate of **#184**, or
  - rename **#182** into a follow-up hardening issue

### Action B — Strengthen epic indexing
- Update **#266** description with grouped child issue lists
- Optionally update **#173** and **#174** descriptions with explicit child-ticket breakdown
- Add tighter scope boundaries to **#175**

### Action C — Improve naming clarity
- Optionally rename **#171** to include navigation / role matrix emphasis
- Optionally rename **#172** to include trust states / verification wording

### Action D — Reduce backlog ambiguity
- Mark #204 as follow-up hardening
- Consider whether #110 is better labeled `type:feature` or `type:hardening`
- If #173 lacks concrete sub-issues, create them before implementation starts

---

## Recommended cleanup order

### Step 1
Resolve true duplicates first:
- #277 vs #278
- #182 vs #184

### Step 2
After duplicates are resolved, update epic descriptions:
- #266
- #173
- #174
- #175

### Step 3
Then apply milestone + labels cleanup according to:
- `docs/github_milestones.md`
- `docs/github_issue_assignment_plan.md`

### Step 4
Only after that, do optional title refinements for #171 / #172 if still useful.

Why this order:
сначала убрать зеркала, потом укрепить скелет, потом красить вывески.

---

## Compact verdict by issue

| Issue | Verdict |
| --- | --- |
| #175 | Keep, but narrow and clarify scope boundaries |
| #204 | Keep as small hardening follow-up |
| #266 | Keep as main umbrella epic, strengthen child indexing |
| #277 | Close as duplicate of #278 |
| #278 | Keep as primary migration issue |
| #110 | Keep, possibly reclassify as hardening if desired |
| #171 | Keep, optional title tightening |
| #172 | Keep, optional title tightening |
| #173 | Keep, but add explicit child implementation tickets |
| #174 | Keep, but clarify concrete sub-issue structure |
| #182 | Prefer close as duplicate of #184, else narrow to follow-up hardening |
| #184 | Keep as primary feed photo upload issue |

---

## Note

Хороший cleanup не должен превращаться в косметический марафон. Для BazarDrive самое ценное сейчас:
- убрать реальные дубли;
- сделать epic-структуру читаемой;
- не позволить quality/trust/compliance задачам расплыться в бесконечные meta-контейнеры.

Иными словами: меньше тумана, больше опорных столбов.
