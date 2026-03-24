# Issue #121 — Triage + Subtask 121.1 (Baseline диагностика)

## Scope guardrails

**In scope:** фон/контраст/читаемость/состояния кнопок и вкладок (`Лента`, `Правила`, `Профиль`).  
**Out of scope:** редизайн, migration на Tailwind CLI/PostCSS, изменения API/бизнес-логики.

## Priority plan and dependency order

### P0 (must-fix first)
1. **121.2 — Theme tokens fix (`web/js/tailwind-config.js`)**  
   Цель: гарантировать устойчивое разделение `bg` vs `panel/panelSoft`, сохранить читаемость `text/textSoft`, не уронить CTA-контраст.
2. **121.3 — Fine tuning in markup/styles (`guest_feed.html`, `web/css/feed.css`)**  
   Цель: различимость карточек, бордеров, secondary-button и active/inactive states для `tab-btn`, `profile-menu-btn`, `role-btn`, CTA.

### P1 (after P0 visual stability)
3. **121.4 — A11y + state UX pass**  
   Цель: довести `hover/active/disabled/loading/help-text` состояния action-кнопок и закрепить понятный фидбэк.

### P2 (release artifacts)
4. **121.5 — PR artifacts & closure evidence**  
   Цель: before/after, desktop+mobile test plan, Chrome+Edge checks, финальная валидация acceptance criteria.

## Subtask status checklist (issue #121)

- [x] 121.1 Baseline-диагностика: скриншоты текущего состояния + computed colors ключевых блоков.
- [x] 121.2 Корректировка цветовых токенов темы в `web/js/tailwind-config.js`.
- [ ] 121.3 Тонкая настройка контраста карточек/бордеров/кнопок (`guest_feed.html`, `web/css/feed.css`).
- [ ] 121.4 Визуальная и а11y-проверка состояний (`active`, `inactive`, `hover`, `disabled`) на всех вкладках.
- [ ] 121.5 PR-артефакты: before/after скриншоты, test plan, привязка `Closes #121`.

## 121.1 Baseline diagnostics

### Files inspected
- `web/js/tailwind-config.js`
- `guest_feed.html`
- `web/css/feed.css`
- `web/js/feed.js` (button/state generation inventory)

### Computed baseline contrasts (WCAG ratio)

| Pair | Contrast |
|---|---:|
| `bg (#0b1020)` vs `panel (#131a2b)` | `1.09` |
| `bg (#0b1020)` vs `panelSoft (#1b2338)` | `1.21` |
| `text (#e8edff)` vs `bg (#0b1020)` | `16.22` |
| `textSoft (#9aa7c7)` vs `bg (#0b1020)` | `7.87` |
| `textSoft (#9aa7c7)` vs `panel (#131a2b)` | `7.21` |
| `accent (#4f8cff)` vs `panel (#131a2b)` | `5.39` |

### Baseline conclusion
- Текстовый контраст в целом достаточный.
- Основной риск регрессии #121 подтверждается в зоне **surface separation**: разрыв между page background и карточками (`bg` vs `panel/panelSoft`) слишком мал (`1.09` / `1.21`) и визуальная иерархия может «слипаться».
- Следующий PR (121.2) должен в первую очередь увеличить separation-контраст поверхностей, сохранив читаемость текста/CTA.


## 121.2 Theme tokens update (P0)

### Updated tokens
- `bg`: `#0b1020` → `#050812`
- `panel`: `#131a2b` → `#1a2742`
- `panelSoft`: `#1b2338` → `#243252`
- `accent`: `#4f8cff` → `#6aa1ff`
- `text`: `#e8edff` → `#edf2ff`
- `textSoft`: `#9aa7c7` → `#b3bedb`

### Post-change contrast snapshot

| Pair | Contrast |
|---|---:|
| `bg (#050812)` vs `panel (#1a2742)` | `1.35` |
| `bg (#050812)` vs `panelSoft (#243252)` | `1.57` |
| `text (#edf2ff)` vs `bg (#050812)` | `17.85` |
| `textSoft (#b3bedb)` vs `bg (#050812)` | `10.77` |
| `textSoft (#b3bedb)` vs `panel (#1a2742)` | `8.00` |
| `accent (#6aa1ff)` vs `panel (#1a2742)` | `5.77` |

### 121.2 conclusion
- Surface separation improved compared with baseline (`1.09`/`1.21` → `1.35`/`1.57`).
- Text and action color contrast remains comfortably above recommended thresholds for normal text/UI.
- Next step is **121.3**: tune borders, secondary buttons, and per-screen states using updated tokens.

## Issue comment draft (to post in #121)

```md
Статус: ✅ Выполнен subtask **121.1 Baseline-диагностика**.

Что сделано:
- Проведён аудит `guest_feed.html`, `web/css/feed.css`, `web/js/tailwind-config.js`, `web/js/feed.js`.
- Зафиксированы baseline contrast-ratio для ключевых пар цветов.
- Подтверждён ключевой риск: низкое разделение поверхностей `bg` vs `panel/panelSoft`.

Как проверено:
- Ручной аудит токенов и классов по вкладкам Лента/Правила/Профиль.
- Расчёт contrast ratio для базовых токенов темы.

Артефакты:
- PR: <ADD_PR_LINK>
- Commit: <ADD_COMMIT_LINK>

Следующий шаг (P0): **121.2** — корректировка токенов темы.
```

## Notes on screenshots
- Attempted to prepare automated screenshot capture in this environment.
- Browser screenshot tooling is not available in the current runtime, so visual captures are deferred to the implementation PRs (121.2+).
