# GitHub Manual Execution Checklist for BazarDrive

## Purpose

Этот документ содержит **пошаговый manual execution checklist** для наведения порядка в GitHub backlog проекта **BazarDrive**.

Он нужен, чтобы:
- пройти cleanup без хаоса и пропусков;
- разложить roadmap по milestone-ам и labels;
- зафиксировать единый порядок действий;
- не держать всю последовательность в голове.

Связанные документы:
- `docs/roadmap.md`
- `docs/github_milestones.md`
- `docs/github_milestone_descriptions.md`
- `docs/github_labels.md`
- `docs/github_issue_assignment_plan.md`
- `docs/github_cleanup_plan.md`
- `docs/github_cleanup_comments.md`

---

## Recommended execution order

Работать лучше именно в этом порядке:

1. создать milestone-ы;
2. создать labels;
3. убрать дубли и cleanup ambiguity;
4. обновить epic descriptions;
5. назначить milestone-ы issues;
6. назначить labels issues;
7. сделать финальную sanity check.

Почему так:
- сначала создаются контейнеры;
- потом упрощается backlog;
- потом задачи раскладываются по системе;
- только после этого имеет смысл проверять целостность.

---

# Phase 0 — Preparation

## 0.1 Open the reference docs

- [ ] Открыть `docs/roadmap.md`
- [ ] Открыть `docs/github_milestones.md`
- [ ] Открыть `docs/github_milestone_descriptions.md`
- [ ] Открыть `docs/github_labels.md`
- [ ] Открыть `docs/github_issue_assignment_plan.md`
- [ ] Открыть `docs/github_cleanup_plan.md`
- [ ] Открыть `docs/github_cleanup_comments.md`

## 0.2 Confirm target repo

- [ ] Убедиться, что работа идёт в `MrZelus/BazarDrive`
- [ ] Проверить, что открыты именно **issues**, а не pull requests
- [ ] Проверить, что есть права на изменение backlog metadata

---

# Phase 1 — Create milestones

## 1.1 Create milestone Wave A

- [ ] Создать milestone: `Wave A — Compliance Core & Release Readiness`
- [ ] Вставить описание из `docs/github_milestone_descriptions.md`

## 1.2 Create milestone Wave B

- [ ] Создать milestone: `Wave B — Driver Readiness UX`
- [ ] Вставить описание из `docs/github_milestone_descriptions.md`

## 1.3 Create milestone Wave C

- [ ] Создать milestone: `Wave C — Compliance Automation & Moderation`
- [ ] Вставить описание из `docs/github_milestone_descriptions.md`

## 1.4 Create milestone Wave D

- [ ] Создать milestone: `Wave D — Feed, Trust & Role UX Hardening`
- [ ] Вставить описание из `docs/github_milestone_descriptions.md`

## 1.5 Quick milestone check

- [ ] Проверить, что все 4 milestone-а видны в списке
- [ ] Проверить названия на一致ность с docs
- [ ] Проверить, что descriptions вставились без обрезания важных блоков

---

# Phase 2 — Create labels

## 2.1 Create minimal priority labels

- [ ] `priority:p0`
- [ ] `priority:p1`
- [ ] `priority:p2`
- [ ] `priority:p3`

## 2.2 Create minimal type labels

- [ ] `type:epic`
- [ ] `type:feature`
- [ ] `type:tech`
- [ ] `type:bug`
- [ ] `type:hardening`
- [ ] `type:test`
- [ ] `type:docs`
- [ ] `type:ux`
- [ ] `type:security`

## 2.3 Create minimal domain labels

- [ ] `domain:driver`
- [ ] `domain:compliance`
- [ ] `domain:feed`
- [ ] `domain:moderation`
- [ ] `domain:quality`
- [ ] `domain:auth`
- [ ] `domain:docs`
- [ ] `domain:web`
- [ ] `domain:orders`
- [ ] `domain:bot` if needed now

## 2.4 Create layer labels

- [ ] `layer:db`
- [ ] `layer:model`
- [ ] `layer:repository`
- [ ] `layer:service`
- [ ] `layer:api`
- [ ] `layer:web`
- [ ] `layer:bot`
- [ ] `layer:test`
- [ ] `layer:docs`
- [ ] `layer:ops`

## 2.5 Optional status labels

- [ ] `status:ready`
- [ ] `status:needs-spec`
- [ ] `status:blocked`
- [ ] `status:in-review`
- [ ] `status:follow-up`

## 2.6 Label sanity check

- [ ] Проверить, что нет дублирующихся названий с разным регистром
- [ ] Проверить, что colors и descriptions заведены
- [ ] Проверить, что каталог labels соответствует `docs/github_labels.md`

---

# Phase 3 — Resolve duplicates and overlap

## 3.1 Resolve #277 vs #278

- [ ] Открыть #277
- [ ] Открыть #278
- [ ] Сравнить, нет ли уникального контекста в #277
- [ ] Если уникальный контекст есть, перенести его в #278
- [ ] Добавить duplicate comment из `docs/github_cleanup_comments.md`
- [ ] Закрыть #277 как duplicate of #278

## 3.2 Resolve #182 vs #184

- [ ] Открыть #182
- [ ] Открыть #184
- [ ] Сравнить scope и уже имеющийся discussion
- [ ] Выбрать стратегию:
  - [ ] закрыть #182 как duplicate of #184
  - [ ] либо сузить #182 до follow-up hardening
- [ ] Добавить соответствующий comment из `docs/github_cleanup_comments.md`
- [ ] Обновить title/labels #182, если выбран follow-up path

## 3.3 Quick duplicate check

- [ ] Проверить, что явные дубли больше не висят открытыми без решения
- [ ] Проверить, что primary issue для каждого спорного направления понятен

---

# Phase 4 — Update epic descriptions

## 4.1 Update #266

- [ ] Открыть #266
- [ ] Вставить ready block для grouped child issue structure из `docs/github_cleanup_comments.md`
- [ ] Проверить, что в epic видны разделы:
  - backend foundation
  - driver-facing readiness
  - automation and moderation
  - order-flow integration

## 4.2 Update #173

- [ ] Открыть #173
- [ ] Добавить ready block с recommended child issue directions
- [ ] Проверить, что epic не выглядит как одиночная implementation task

## 4.3 Update #174

- [ ] Открыть #174
- [ ] Добавить ready block с concrete child issue directions
- [ ] Убедиться, что #110 явно читается как один из concrete tickets

## 4.4 Update #175

- [ ] Открыть #175
- [ ] Добавить scope-boundary block из `docs/github_cleanup_comments.md`
- [ ] Проверить, что есть разделы `In scope for the current roadmap phase` и `Out of scope for now`

## 4.5 Optional epic title tightening

### #171
- [ ] Решить, нужно ли rename:
  - current: `Epic: Publication Profile & Role UX`
  - suggested: `Epic: Publication Profile, Role Matrix & Navigation UX`

### #172
- [ ] Решить, нужно ли rename:
  - current: `Epic: Documents & Trust Layer`
  - suggested: `Epic: Documents, Trust States & Verification UX`

---

# Phase 5 — Assign milestones

## 5.1 Assign Wave A

- [ ] #175 -> Wave A
- [ ] #204 -> Wave A
- [ ] #266 -> Wave A
- [ ] #278 -> Wave A
- [ ] #279 -> Wave A
- [ ] #280 -> Wave A
- [ ] #281 -> Wave A
- [ ] #282 -> Wave A
- [ ] #283 -> Wave A
- [ ] #285 -> Wave A

## 5.2 Assign Wave B

- [ ] #267 -> Wave B
- [ ] #268 -> Wave B
- [ ] #269 -> Wave B
- [ ] #270 -> Wave B
- [ ] #272 -> Wave B
- [ ] #273 -> Wave B

## 5.3 Assign Wave C

- [ ] #274 -> Wave C
- [ ] #275 -> Wave C
- [ ] #276 -> Wave C
- [ ] #284 -> Wave C

## 5.4 Assign Wave D

- [ ] #110 -> Wave D
- [ ] #171 -> Wave D
- [ ] #172 -> Wave D
- [ ] #173 -> Wave D
- [ ] #174 -> Wave D
- [ ] #177 -> Wave D
- [ ] #182 -> Wave D if still open
- [ ] #184 -> Wave D

## 5.5 Milestone sanity check

- [ ] Проверить, что у всех перечисленных задач есть milestone
- [ ] Проверить, что issue не assigned в неверную волну
- [ ] Проверить, что закрытые duplicate issues не мешают milestone overview

---

# Phase 6 — Assign labels

## 6.1 Assign Wave A labels

- [ ] #175 -> `type:epic`, `priority:p1`, `domain:quality`, `domain:docs`, `layer:docs`
- [ ] #204 -> `type:hardening`, `priority:p1`, `domain:quality`, `domain:docs`, `layer:test`
- [ ] #266 -> `type:epic`, `priority:p0`, `domain:driver`, `domain:compliance`
- [ ] #278 -> `type:tech`, `priority:p0`, `domain:compliance`, `layer:db`
- [ ] #279 -> `type:tech`, `priority:p0`, `domain:compliance`, `layer:model`
- [ ] #280 -> `type:tech`, `priority:p0`, `domain:compliance`, `layer:repository`
- [ ] #281 -> `type:tech`, `priority:p0`, `domain:driver`, `domain:compliance`, `layer:service`
- [ ] #282 -> `type:tech`, `priority:p0`, `domain:compliance`, `domain:web`, `layer:api`
- [ ] #283 -> `type:tech`, `priority:p0`, `domain:compliance`, `domain:orders`, `layer:service`
- [ ] #285 -> `type:test`, `priority:p0`, `domain:quality`, `domain:compliance`, `layer:test`

## 6.2 Assign Wave B labels

- [ ] #267 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:web`
- [ ] #268 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:web`
- [ ] #269 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:web`
- [ ] #270 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:web`
- [ ] #272 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `domain:orders`, `layer:web`
- [ ] #273 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `type:ux`, `layer:web`

## 6.3 Assign Wave C labels

- [ ] #274 -> `type:feature`, `priority:p2`, `domain:orders`, `domain:compliance`, `layer:service`
- [ ] #275 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:ops`
- [ ] #276 -> `type:feature`, `priority:p1`, `domain:moderation`, `domain:compliance`, `layer:web`
- [ ] #284 -> `type:tech`, `priority:p1`, `domain:compliance`, `layer:ops`

## 6.4 Assign Wave D labels

- [ ] #110 -> `type:feature` or `type:hardening`, `priority:p2`, `domain:feed`, `domain:auth`, `layer:api`
- [ ] #171 -> `type:epic`, `priority:p2`, `domain:web`, `domain:feed`, `type:ux`
- [ ] #172 -> `type:epic`, `priority:p2`, `domain:feed`, `domain:compliance`, `type:ux`
- [ ] #173 -> `type:epic`, `priority:p2`, `domain:feed`, `layer:web`
- [ ] #174 -> `type:epic`, `priority:p2`, `domain:moderation`, `domain:auth`, `type:security`
- [ ] #177 -> `type:feature`, `priority:p2`, `domain:web`, `type:ux`, `layer:web`
- [ ] #182 -> `type:hardening`, `status:follow-up`, `priority:p3`, `domain:feed`, `domain:web`, `layer:web` if kept open as follow-up
- [ ] #184 -> `type:feature`, `priority:p3`, `domain:feed`, `domain:web`, `layer:web`

## 6.5 Label sanity check

- [ ] Проверить, что у каждой открытой задачи есть priority label
- [ ] Проверить, что у каждой открытой задачи есть type label
- [ ] Проверить, что у каждой открытой задачи есть минимум один domain label
- [ ] Проверить, что labels не конфликтуют между собой

---

# Phase 7 — Final sanity check

## 7.1 Review milestone boards mentally

- [ ] Wave A выглядит как compliance backend core, а не как смесь всего подряд
- [ ] Wave B выглядит как driver readiness UX, а не как backend sprint
- [ ] Wave C выглядит как automation/moderation wave
- [ ] Wave D выглядит как publication/feed hardening wave

## 7.2 Review issue clarity

- [ ] У каждого спорного направления есть один primary issue
- [ ] Epic-issues читаются как umbrella-структуры
- [ ] Нет открытых явных дублей без комментариев
- [ ] Cross-cutting issues (#175, #204) не выглядят бесконечными sink-ами

## 7.3 Review label hygiene

- [ ] Нет очевидного overlabeling
- [ ] Labels помогают triage, а не шумят
- [ ] Можно быстро отфильтровать backlog по milestone / domain / priority

## 7.4 Optional snapshot

- [ ] Сделать screenshot milestone list
- [ ] Сделать screenshot issue list with labels
- [ ] Сохранить как reference перед следующей roadmap итерацией

---

# Fast-track version

Если нужно пройтись очень быстро, минимальный маршрут такой:

- [ ] Создать 4 milestone-а
- [ ] Создать priority + type + domain labels
- [ ] Закрыть #277 как duplicate of #278
- [ ] Решить #182 vs #184
- [ ] Обновить #266, #173, #174, #175
- [ ] Назначить milestone-ы всем текущим roadmap issues
- [ ] Назначить priority labels
- [ ] Назначить domain/type labels
- [ ] Проверить, что backlog стал читаемым

---

# Completion criteria

Checklist можно считать завершённым, если:

- [ ] milestone-ы созданы
- [ ] labels созданы
- [ ] duplicate issues обработаны
- [ ] epic descriptions усилены
- [ ] active issues назначены по roadmap waves
- [ ] labels отражают реальный смысл задач
- [ ] backlog читается как управляемая система, а не как россыпь постановок

---

## Note

Хороший manual execution checklist должен убирать лишние решения по ходу работы. Этот документ специально сделан так, чтобы GitHub cleanup шёл как маршрут с указателями, а не как блуждание по лесу issue-ов с фонариком на последнем проценте батареи.
