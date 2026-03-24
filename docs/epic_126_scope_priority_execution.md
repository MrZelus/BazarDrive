# Epic #126 — Scope priorities and execution order

## A) Priority matrix (item → priority → rationale)

| Scope item | Priority | Why this priority | Expected deliverable | Likely files/areas touched | Verification method |
|---|---|---|---|---|---|
| 1) Централизация и консистентное использование токенов темы | **P0** | Это базовый источник правды для всех остальных задач. Пока токены применяются неравномерно, состояния и регрессии будут нестабильны и дороги в поддержке. | Token-consistency baseline: критичные экраны (`Лента/Правила/Профиль`) используют только утвержденные theme tokens; найденный drift зафиксирован как остаток работ. | `web/js/tailwind-config.js`, UI-шаблоны/компоненты в `web/**`, локальные стили в `web/css/**` где есть legacy/hardcoded значения. | 1) Статический проход по usage (token vs hardcoded). 2) Визуальный smoke на `Лента/Правила/Профиль` (desktop/mobile, Chrome/Edge). 3) Выборочная проверка контраста для текст/фон и CTA-пар. |
| 2) Унификация состояний компонентов: `default/hover/active/disabled/loading` | **P1** | Состояния должны строиться поверх уже централизованных токенов. Если делать раньше P0, получится повторная переработка и рассинхрон состояний между компонентами. | Единая state-matrix для базовых интерактивных компонентов (минимум: кнопки/табы) с одинаковой визуальной логикой в ключевых экранах. | Библиотека/shared UI в `web/**` (кнопки, табы, utility-классы состояний), возможно общие стили в `web/css/**`. | 1) Проверка каждого состояния по матрице. 2) Keyboard/mouse/touch проверка интерактивов. 3) Cross-browser в Chrome/Edge + mobile emulation. |
| 3) Регрессионный визуальный чеклист (desktop/mobile, Chrome/Edge) | **P1** | Нужен сразу после стабилизации токенов/состояний, чтобы закрепить результат и ловить откаты в следующих PR. Это процессный guardrail, а не первичный фундамент. | Документированный и воспроизводимый checklist/runbook + шаблон отчета прогона по матрице устройств/браузеров. | `docs/` (чеклист, runbook), при необходимости PR-шаблоны в `.github/`. | 1) Полный dry-run чеклиста на ключевых страницах. 2) Артефакт отчета: pass/fail + найденные отклонения. 3) Повторяемость другим участником команды. |
| 4) Документированный Theme Contract в `docs/` | **P2** | Документация должна фиксировать уже подтвержденные решения P0/P1. Если писать слишком рано, контракт устареет до завершения рефакторинга. | `Theme Contract` v1: список разрешенных токенов, state rules, do/don’t примеры, ссылка на regression protocol для UI PR. | `docs/theme-contract.md` (или аналогичный файл в `docs/`), возможно `docs/contributing.md`/PR template для обязательной ссылки на контракт. | 1) Док-ревью по полноте (tokens + states + regression). 2) Выборочная сверка контракта с фактической реализацией на `Лента/Правила/Профиль`. |

---

## B) Dependency order

Жесткий порядок зависимостей:

1. **Item 1 (P0: tokens)** →
2. **Item 2 (P1: states)** →
3. **Item 3 (P1: regression checklist)** →
4. **Item 4 (P2: Theme Contract docs)**

Кратко по зависимостям:
- **2 зависит от 1**: матрица состояний должна использовать централизованные токены, иначе будет повторный рефакторинг.
- **3 зависит от 1+2**: чеклист должен валидировать уже зафиксированное целевое поведение, а не «плавающую» реализацию.
- **4 зависит от 1+2+3**: контракт в docs должен документировать стабильную практику и проверяемый процесс.

---

## C) Recommended execution sequence + first PR candidate

Рекомендуемая последовательность (first → fourth):

1. **First:** Item 1 — token centralization consistency pass.
2. **Second:** Item 2 — unified component states matrix implementation.
3. **Third:** Item 3 — visual regression checklist + first formal run.
4. **Fourth:** Item 4 — finalize Theme Contract documentation.

### Recommended first PR candidate

**Title:** `Part of #126: Enforce theme token consistency on Feed/Rules/Profile`

**Почему именно этот PR первым**
- Максимально снижает риск повторных правок в P1.
- Дает измеримый baseline для состояний и регрессий.
- Полностью в рамках scope (без redesign/API/CLI-migration).

**Что должно войти в PR-1**
- Выравнивание использования токенов на критичных экранах.
- Фиксация остаточного drift (если есть) как follow-up списком.
- Короткий verification summary по matrix: desktop/mobile + Chrome/Edge.

---

## D) Risks if the order is violated

- **Сначала states без token-centralization:** двойная работа и визуальные расхождения между компонентами при последующей миграции токенов.
- **Сначала regression checklist до стабилизации UI:** высокий шум false-positive/false-negative, т.к. эталон еще не определен.
- **Сначала Theme Contract docs:** документация быстро устареет и потеряет доверие команды.
- **Итоговый системный риск:** возврат к ad-hoc фиксам (проблема, которую Epic #126 как раз должен устранить).
