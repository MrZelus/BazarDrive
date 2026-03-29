# BazarDrive System Health Dashboard

Этот документ — **живой шаблон контроля состояния проекта**.

Его задача: не просто перечислять задачи, а показывать, насколько проект остаётся:
- управляемым;
- согласованным между docs / code / roles / tests;
- дисциплинированным по PR и lifecycle;
- прозрачным по ownership.

Dashboard нужен для раннего обнаружения проблем в процессе развития проекта.

---

## 1. Как использовать этот dashboard

Использовать документ как регулярную контрольную панель:
- при weekly review;
- при review больших Epic-ов;
- перед merge крупных PR;
- при разборе конфликтов между docs, bot, API и data layer.

Рекомендуемый формат обновления:
- обновлять вручную при значимых изменениях;
- пересматривать минимум раз в неделю;
- использовать вместе с:
  - `docs/operating_board.md`
  - `docs/project_operating_plan.md`
  - `docs/security/permissions_matrix.md`

---

## 2. Базовые метрики system health

Ниже — стартовый набор из 12 метрик.

| # | Metric | Why it matters | Current status | Target | Action if red |
|---|---|---|---|---|---|
| 1 | Open PR count | Показывает текущую нагрузку review/process | TBD | manageable | Упростить scope, закрыть зависшие PR |
| 2 | PR without issue link | Ломает traceability lifecycle | TBD | 0 | Требовать issue linkage |
| 3 | PR without docs update where docs are expected | Показывает docs drift | TBD | 0 | Обновить docs или объяснить why not |
| 4 | Conflict PR count | Сигнал плохой branch hygiene / oversized scope | TBD | 0 | Rebase/split PR |
| 5 | Oversized PR count | Признак смешанного scope | TBD | low | Делить на smaller PRs |
| 6 | Issues without owner | Показывает ownership gaps | TBD | 0 | Назначить owner |
| 7 | Epics without responsible owner | Ломает governance | TBD | 0 | Зафиксировать accountable owner |
| 8 | Role/compliance changes without permissions sync | Риск логических багов и security drift | TBD | 0 | Обновить permissions/docs |
| 9 | Merged PR without verification notes | Ломает review discipline | TBD | 0 | Стандартизировать PR template |
| 10 | API changes without OpenAPI/docs sync | Ломает контракты и интеграцию | TBD | 0 | Обновить docs/openapi |
| 11 | Lifecycle breaks by stage | Показывает, где система разваливается | TBD | visible and decreasing | Разобрать stage and patch process |
| 12 | Domains without clear owner | Риск скрытого долга | TBD | 0 | Закрепить ownership |

---

## 3. PR Health

### What to track
- сколько open PR;
- сколько PR без issue link;
- сколько PR без описания по template;
- сколько PR конфликтных;
- сколько PR зависли без review;
- сколько PR затрагивают слишком много слоёв сразу.

### Interpretation
- много open PR = bottleneck в review;
- много conflict PR = плохая веточная дисциплина;
- много oversized PR = project теряет scope control.

### Quick review questions
- PR связан с issue?
- PR касается только своего scope?
- PR изменяет docs, если должен?
- reviewer сможет быстро понять diff?

---

## 4. Docs Sync Health

### What to track
- role/permissions changes без обновления `permissions_matrix`;
- API changes без обновления `docs/openapi.yaml`;
- flow/UI changes без обновления flow docs;
- governance/process changes без обновления `contributing.md` или `operating_board.md`.

### Interpretation
Docs drift — один из главных сигналов, что проект начинает расходиться сам с собой.

### Related docs
- `docs/contributing.md`
- `docs/security/permissions_matrix.md`
- `docs/project_operating_plan.md`
- `docs/operating_board.md`
- `docs/openapi.yaml`

---

## 5. Ownership Health

### What to track
- tasks without owner;
- epics without owner;
- PR without reviewer;
- domains without clear accountable person.

### Interpretation
Если у задачи нет owner, она становится зоной размывания ответственности.
Если у домена нет owner, там почти наверняка копится скрытый долг.

### Expected domains with owners
- docs
- web
- API
- bot
- data / migrations
- RBAC / security
- moderation / compliance
- tests / QA
- release / merge

---

## 6. Lifecycle Health

Идеальный lifecycle:

`idea -> issue -> docs/design -> code -> tests -> PR -> review -> merge -> updated system state`

### Where lifecycle can break

| Stage | Signal of break |
|---|---|
| Idea -> Issue | код/PR есть, issue нет |
| Issue -> Docs | issue есть, docs/contracts не обновлены |
| Docs -> Code | docs описывают flow, которого нет в коде |
| Code -> Tests | изменение есть, проверки нет |
| Tests -> PR | verification section пустая |
| PR -> Review | PR без owner/reviewer |
| Review -> Merge | merge blocked conflicts / oversized scope |
| Merge -> Updated system | код в main есть, а docs / board / flows устарели |

### What to do
При каждом detected break фиксировать:
- stage;
- причина;
- affected domain;
- corrective action.

---

## 7. RBAC / Role / Compliance Health

### What to track
- role changes without docs sync;
- compliance changes without test coverage;
- driver eligibility changes without permissions/guard updates;
- moderator/admin boundary changes without explicit review.

### Why it matters
Для BazarDrive role/compliance drift особенно опасен, потому что ломает:
- доступы;
- допуск водителей;
- moderation decisions;
- user expectations.

### Related doc
- `docs/security/permissions_matrix.md`

---

## 8. Quality / Delivery Health

### What to track
- smoke coverage критичных флоу;
- regression-sensitive PR;
- docs-only PR vs mixed PR;
- PR merge readiness;
- recent follow-up fixes after merge.

### Why it matters
Main должен быть не просто рабочим, а предсказуемым.

---

## 9. Suggested dashboard statuses

Можно использовать простую систему:
- **Green** — метрика под контролем
- **Yellow** — есть риск, но он понятен
- **Red** — нужно вмешательство

Пример рабочего формата:

| Area | Status | Note |
|---|---|---|
| PR health | TBD | review later |
| Docs sync | TBD | update after PR audit |
| Ownership | TBD | check issue assignment |
| Lifecycle | TBD | inspect recent PRs |
| RBAC / Compliance | TBD | compare with permissions matrix |
| Quality / Delivery | TBD | audit smoke/regression discipline |

---

## 10. Review ritual

Рекомендуемый ритм:

### Weekly
- просмотреть open PR;
- проверить конфликтные ветки;
- посмотреть issues without owner;
- проверить docs drift;
- обновить dashboard notes.

### Before merging large PR
- проверить lifecycle completeness;
- проверить docs sync;
- проверить role/RBAC impact;
- проверить, не oversized ли PR.

### After merging system-impacting PR
- обновить related docs;
- обновить board/plan при необходимости;
- проверить, не появился ли lifecycle break post-merge.

---

## 11. Related project control documents

Этот dashboard должен использоваться вместе с:
- `docs/operating_board.md`
- `docs/project_operating_plan.md`
- `docs/security/permissions_matrix.md`
- `docs/contributing.md`

И вместе с визуальными картами:
- lifecycle map
- governance map
- RACI map
- operating board

---

## 12. First recommended next actions

1. Заполнить стартовые значения по 12 базовым метрикам
2. Отметить open PR without issue / without docs sync
3. Найти issues / epics without owner
4. Сверить recent role/compliance changes с `permissions_matrix`
5. Использовать dashboard как weekly review sheet

---

BazarDrive становится сильнее не только от новых фич, а от способности видеть, где система теряет форму. Этот dashboard нужен именно для этого.
