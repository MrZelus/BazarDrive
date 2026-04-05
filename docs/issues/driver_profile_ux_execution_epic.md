# Epic: UX-пересборка водительского профиля (Driver Profile v2)

## Цель

Собрать экран водительского профиля так, чтобы водитель за **3–5 секунд** понимал:
- готов ли он к заказам;
- что уже заполнено;
- чего не хватает;
- какое следующее действие главное.

## Контекст проблемы

Текущий экран перегружен равнозначными блоками и дублирующими CTA, из-за чего:
- «готовность к заказам» не читается сразу;
- документы и допуск конкурируют визуально;
- следующий шаг теряется;
- мобильный экран перегружается длинными требованиями;
- в UI могут попадать технические ошибки.

## Product outcome

После внедрения v2:
1. В верхней части экрана всегда есть понятный summary (Hero + Status).
2. Для `blocked/in_progress` всегда показаны причина и конкретный next step.
3. Есть единый sticky primary CTA, без дублей в середине экрана.
4. Активный путевой лист всегда приоритезирован в документах.
5. Progress/readiness синхронизированы с серверным summary-контрактом.

---

## Scope (P1 → P4)

### P1 — Core onboarding visibility

#### 1) Hero-card
**Что делаем**
- Единый верхний блок с: аватаром, ФИО, ролью `Водитель`, формой деятельности, налоговым режимом.
- Отдельный заметный прогресс (`filled/total`, например `4/11`).
- Один главный CTA: `Начать заполнение` / `Продолжить заполнение`.

**Acceptance criteria**
- [ ] Hero-card виден без прокрутки на mobile.
- [ ] На экране только один primary CTA.
- [ ] Поля role/business/tax не размазаны по другим summary-блокам.

#### 2) Status-card допуска
**Что делаем**
- Карточка сразу под Hero c состоянием readiness:
  - `ready`
  - `in_progress`
  - `blocked`
  - `pending_review`
- Для `blocked` и `in_progress`: обязательны `reason` + `next_action`.
- Визуальные стили по severity: `success`, `warning`, `pending`, `blocked`.

**Acceptance criteria**
- [ ] Для неготового статуса всегда есть человеко-понятная причина.
- [ ] Для неготового статуса всегда есть конкретный следующий шаг.
- [ ] Цвет/стиль Status-card зависит от нормализованного статуса.

#### 3) Checklist обязательных полей
**Что делаем**
- Компактный чеклист обязательных полей:
  - фамилия, имя, отчество, телефон, email,
  - категория ВУ, стаж, мед. ограничения, судимость, штрафы,
  - тип занятости.
- Каждый пункт имеет явное состояние:
  - `complete`
  - `actionable`
- Тап по `actionable` ведёт в конкретный раздел формы.

**Acceptance criteria**
- [ ] Есть счётчик прогресса checklist.
- [ ] Заполненные/незаполненные поля визуально разделены.
- [ ] Для каждого missing-пункта доступен deeplink к исправлению.

#### 4) Readiness summary API + blocking reasons
**Что делаем (backend)**
- В summary-ответе профиля вернуть:
  - `readiness_status`
  - `progress_filled`
  - `progress_total`
  - `blocking_reasons[]`
  - `next_step`
  - `allowed_actions[]`
- Для каждого blocking reason:
  - `code`
  - `message`
  - `severity`
  - `next_action`
  - `target_screen`

**Acceptance criteria**
- [ ] Frontend строит Status-card и CTA только из серверного summary.
- [ ] Readiness не вычисляется «на глаз» во view-логике.
- [ ] Есть контрактные тесты на blocking reasons.

---

### P2 — Documents-first safety flow

#### 5) Секция документов с приоритетом активного путевого листа
**Что делаем**
- Порядок в секции документов:
  1. Активный путевой лист
  2. Обязательные документы
  3. На проверке
  4. Подтверждённые
  5. Архив/история
- Отдельная `priority-card` для активного путевого листа.
- Document-card показывает: тип, статус, срок действия, review comment, доступные действия.

**Acceptance criteria**
- [ ] Активный путевой лист всегда выше остальных документов.
- [ ] Для документа доступны `open`, `reupload`, `delete`.
- [ ] Для путевого листа доступно `close waybill`.

#### 6) Нормализация document/review states
**Что делаем (backend + frontend mapping)**
- Нормализовать статусы документа и ревью в единый enum.
- Привязать UI-chip/badge/цвет к нормализованным статусам.

**Acceptance criteria**
- [ ] Нет неоднозначных или дублирующихся статусов.
- [ ] Pending/rejected/approved единообразны во всех карточках.

---

### P3 — Information architecture cleanup

#### 7) Блок «Такси / ИП» как самостоятельный business-profile
**Что делаем**
- Выделить отдельную секцию `business_profile`:
  - форма деятельности, ИНН, ОГРНИП, налоговый режим,
  - регион работы, данные автомобиля.
- Подсвечивать обязательные незаполненные поля.
- Добавить валидации форматов ИНН/ОГРНИП.
- Подключить секцию к readiness logic.

**Acceptance criteria**
- [ ] Business-поля не «хвост» формы и читаются как отдельный блок.
- [ ] Ошибки форматов ИНН/ОГРНИП человеко-понятные.
- [ ] Missing business-данные корректно блокируют readiness (если обязательны).

#### 8) Разделение critical onboarding и publish-profile
**Что делаем**
- Отделить `publish_profile` от критичных для допуска шагов.
- Разрешить пропуск publish-секции, если она не обязательна.

**Acceptance criteria**
- [ ] Publish-профиль не ломает основной onboarding.
- [ ] Readiness для заказов не смешивается с publish-ready (если это отдельная ветка).

#### 9) Единый sticky action bar
**Что делаем**
- Один sticky action-bar на экран:
  - primary: `Добавить документ` или `Продолжить заполнение`
  - secondary: `Ещё`
- Удалить дубли primary CTA из середины страницы.
- Учесть отступ под bottom nav.

**Acceptance criteria**
- [ ] Единственный primary CTA на экране.
- [ ] Sticky bar не перекрывает bottom nav.

#### 10) Empty/loading/error/pending states
**Что делаем**
- Внедрить:
  - empty profile (`0/11`, нет документов)
  - partial profile
  - ready profile (`11/11`)
  - pending review
  - error state c retry
- Добавить skeleton loading.
- Запретить вывод «сырых» технических ошибок (например `Failed to fetch`).

**Acceptance criteria**
- [ ] Все основные состояния имеют человеко-понятный copy.
- [ ] Технические детали скрыты от пользователя.

---

### P4 — Extended domain blocks

#### 11) Выплаты
**Что делаем**
- Компактный блок выплат: статус, способ получения, реквизиты, история начислений.
- Не доминирует в onboarding.

**Acceptance criteria**
- [ ] Если выплаты не обязательны для допуска — не блокируют readiness.
- [ ] Если обязательны — появляются как отдельная blocking reason.

#### 12) Архив документов и microinteractions
**Что делаем**
- Доработать архивную часть, вторичные интеракции и polish.

**Acceptance criteria**
- [ ] Архив документов доступен и не мешает primary flow.

---

## Технические задачи по командам

### Frontend
- [ ] Новый layout driver profile.
- [ ] Компоненты: `HeroCard`, `StatusCard`, `Checklist`, `DocumentCard`, `WaybillPriorityCard`, `StickyActionBar`.
- [ ] Deeplink-навигация из `blocking_reasons.target_screen`.
- [ ] Синхронизация CTA с `allowed_actions`.
- [ ] Human-friendly empty/loading/error states.

### Backend
- [ ] Readiness summary endpoint/section в profile payload.
- [ ] Контракт `blocking_reasons[]`.
- [ ] Документы: upload/reupload/status/review comment/expiry.
- [ ] Ограничение: только один активный путевой лист.
- [ ] Разделение профилей: `basic`, `driver`, `business`, `publish`.

### QA
- [ ] Smoke flow: empty → in_progress → pending_review → ready.
- [ ] Contract tests на readiness summary и blocking reasons.
- [ ] UI regression: единственный primary CTA, приоритет waybill, отсутствие raw errors.
- [ ] Deeplink coverage из status/checklist/document blockers.

---

## Definition of Done (Epic)

Epic считается завершённым, если выполняются все условия:
- [ ] Водитель понимает readiness за 3–5 секунд.
- [ ] Для каждого blocked/in_progress состояния есть причина и next step.
- [ ] Активный путевой лист визуально выделен и выше остальных документов.
- [ ] На экране только один primary CTA.
- [ ] Progress и readiness берутся из серверного summary-контракта.
- [ ] Из blocking reason можно перейти в нужный раздел без ручного поиска.
- [ ] В UI нет сырых технических ошибок.
