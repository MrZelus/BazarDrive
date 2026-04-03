# GitHub Operating Kit Index for BazarDrive

## Purpose

Этот файл — единая точка входа в набор документов по **roadmap, milestones, labels, cleanup и ручному rollout в GitHub** для проекта **BazarDrive**.

Если не хочется вспоминать, какой файл за что отвечает, открывайте сначала этот индекс.

---

## Recommended reading order

### 1. Strategy

#### `docs/roadmap.md`
Использовать, чтобы понять:
- куда движется проект;
- какие есть волны развития;
- что относится к Now / Next / Later / Icebox.

---

### 2. Milestone structure

#### `docs/github_milestones.md`
Использовать, чтобы понять:
- какие milestone-ы нужны в GitHub;
- какие issues входят в каждую волну;
- какие exit criteria у каждого этапа.

#### `docs/github_milestone_descriptions.md`
Использовать, чтобы:
- быстро вставить готовые title + description в GitHub UI при создании milestone-ов.

---

### 3. Labels system

#### `docs/github_labels.md`
Использовать, чтобы:
- завести labels;
- понять naming и color system;
- не превратить backlog в хаотичную наклейку-стену.

---

### 4. Issue assignment

#### `docs/github_issue_assignment_plan.md`
Использовать, чтобы:
- разложить текущие issues по milestone-ам;
- назначить labels;
- быстро провести triage без повторного анализа каждой задачи.

---

### 5. Cleanup

#### `docs/github_cleanup_plan.md`
Использовать, чтобы понять:
- какие issues стоит закрыть как duplicate;
- какие стоит объединить;
- какие epic-issues нужно усилить;
- где нужно сузить scope.

#### `docs/github_cleanup_comments.md`
Использовать, чтобы:
- вставлять готовые комментарии для duplicate/follow-up cleanup;
- быстро обновлять epic descriptions;
- не сочинять тексты вручную каждый раз.

---

### 6. Execution

#### `docs/github_manual_execution_checklist.md`
Использовать, если нужен полный пошаговый manual rollout:
- milestones;
- labels;
- duplicates;
- epic updates;
- milestone assignment;
- label assignment;
- final sanity check.

#### `docs/github_fast_track_checklist.md`
Использовать, если нужен короткий operational маршрут без длинного контекста.

---

## Quick map

| File | Main use |
| --- | --- |
| `docs/roadmap.md` | Общая стратегия и волны развития |
| `docs/github_milestones.md` | Структура milestone-ов |
| `docs/github_milestone_descriptions.md` | Готовые descriptions для GitHub UI |
| `docs/github_labels.md` | Каталог labels |
| `docs/github_issue_assignment_plan.md` | Назначение issues по milestone-ам и labels |
| `docs/github_cleanup_plan.md` | План cleanup backlog |
| `docs/github_cleanup_comments.md` | Готовые cleanup-комментарии и epic update templates |
| `docs/github_manual_execution_checklist.md` | Полный ручной checklist |
| `docs/github_fast_track_checklist.md` | Короткая карманная версия |

---

## Suggested usage modes

### Mode A — Strategy first
Использовать, если нужно сначала понять картину:
1. `docs/roadmap.md`
2. `docs/github_milestones.md`
3. `docs/github_issue_assignment_plan.md`

### Mode B — GitHub setup first
Использовать, если цель — быстро настроить GitHub:
1. `docs/github_milestone_descriptions.md`
2. `docs/github_labels.md`
3. `docs/github_manual_execution_checklist.md`

### Mode C — Backlog cleanup first
Использовать, если хочется начать с уборки:
1. `docs/github_cleanup_plan.md`
2. `docs/github_cleanup_comments.md`
3. `docs/github_issue_assignment_plan.md`

### Mode D — Fast execution
Использовать, если нужно просто пройтись по GitHub без долгого чтения:
1. `docs/github_fast_track_checklist.md`

---

## Practical shortest path

Если нужно минимальное количество чтения перед реальными действиями в GitHub, открывайте только:

1. `docs/github_fast_track_checklist.md`
2. `docs/github_cleanup_comments.md`
3. `docs/github_milestone_descriptions.md`
4. `docs/github_labels.md`

Этого уже достаточно, чтобы:
- создать milestone-ы;
- создать labels;
- закрыть дубли;
- обновить epic-описания;
- раскидать issues по волнам.

---

## Note

Этот индекс нужен для того, чтобы весь набор GitHub-документов работал как один инструментальный комплект, а не как пачка полезных, но разрозненных файлов. Один вход, дальше уже видно, какой ключ подходит к какой двери.
