# Driver Notifications Matrix

Единая матрица уведомлений для driver domain в BazarDrive.

Документ нужен как source of truth для:
- backend event handling;
- Telegram bot notifications;
- frontend in-app alerts/toasts/banners;
- QA сценариев по уведомлениям;
- ограничения шума и дублирования сообщений.

---

## 1. Scope

В документ входят:
- notification events;
- recipients;
- channels;
- priority/severity;
- delivery rules;
- deduplication rules;
- fallback behavior.

В документ не входят:
- конкретные тексты каждого сообщения;
- transport-specific API details;
- дизайн баннеров и toasts.

---

## 2. Notification channels

### 2.1. Telegram bot
Используется для:
- срочных рабочих уведомлений;
- order lifecycle;
- shift-critical actions;
- compliance blockers, требующих быстрого внимания.

### 2.2. Web / in-app
Используется для:
- status banners;
- inline alerts;
- confirmations;
- non-urgent nudges;
- action-required messages на экранах профиля и документов.

### 2.3. System/internal
Используется для:
- audit trail;
- internal logs;
- moderation queues;
- staff/admin attention.

---

## 3. Priority levels

| Priority | Meaning | Typical behavior |
| --- | --- | --- |
| `critical` | требует немедленного внимания | Telegram + in-app blocker |
| `high` | важное рабочее событие | Telegram and/or prominent in-app |
| `medium` | важно, но не срочно | in-app banner/toast, optional Telegram |
| `low` | информационное событие | in-app only or passive history |

---

## 4. General rules

### 4.1. No duplicate storms
Один и тот же доменный event не должен производить несколько одинаковых сообщений в одном канале без причины.

### 4.2. Channel by urgency
- `critical` и `high` обычно идут в Telegram.
- `medium` и `low` обычно остаются в-app, если нет необходимости дёргать пользователя.

### 4.3. State change first, text second
Уведомление строится от canonical event/state change, а не от случайного UI сценария.

### 4.4. Backend is event authority
Backend определяет, когда событие произошло и кому его доставлять.

### 4.5. Respect current context
Если водитель уже находится на нужном экране и видит blocker inline, не всегда нужен дублирующий шумный Telegram.

---

## 5. Profile notifications

| Event | Recipient | Channel | Priority | Notes |
| --- | --- | --- | --- | --- |
| profile_submitted_for_verification | Driver | in-app | medium | подтверждение отправки |
| profile_approved | Driver | Telegram + in-app | high | открывает путь к readiness |
| profile_rejected | Driver | Telegram + in-app | high | требует исправления |
| profile_blocked | Driver | Telegram + in-app blocker | critical | work actions must be blocked |
| profile_unblocked | Driver | Telegram + in-app | high | restore access after correction |

---

## 6. Document notifications

| Event | Recipient | Channel | Priority | Notes |
| --- | --- | --- | --- | --- |
| document_uploaded | Driver | in-app | low | usually no Telegram needed |
| document_under_review | Driver | in-app | low | optional passive status update |
| document_approved | Driver | in-app | medium | Telegram optional if it changes readiness |
| document_rejected | Driver | Telegram + in-app | high | action required |
| document_expiring_soon | Driver | Telegram + in-app | medium | send with cooldown |
| document_expired | Driver | Telegram + in-app blocker | high | affects eligibility |

### Notes
- `document_expiring_soon` должен иметь cooldown, чтобы не спамить каждый день без причины.
- Если несколько документов истекают сразу, лучше агрегировать уведомление.

---

## 7. Trip sheet notifications

| Event | Recipient | Channel | Priority | Notes |
| --- | --- | --- | --- | --- |
| trip_sheet_required_before_shift | Driver | in-app blocker | high | show on go-online attempt |
| trip_sheet_opened | Driver | in-app | low | success confirmation |
| trip_sheet_requires_closing | Driver | Telegram + in-app | high | usually near shift end |
| trip_sheet_closed | Driver | in-app | low | success confirmation |
| trip_sheet_missing_after_shift_end | Driver | Telegram + in-app blocker | high | unresolved compliance action |

---

## 8. Eligibility notifications

| Event | Recipient | Channel | Priority | Notes |
| --- | --- | --- | --- | --- |
| eligibility_ready | Driver | in-app | medium | no need to over-notify |
| eligibility_partially_ready | Driver | in-app | medium | show blockers/remaining steps |
| eligibility_blocked | Driver | Telegram + in-app blocker | critical | cannot go online |
| eligibility_restored | Driver | in-app + optional Telegram | high | when blocker removed |

### Notes
- `eligibility_ready` часто лучше показывать как banner/state, а не как отдельный Telegram ping.
- `eligibility_blocked` должен объяснять ближайший corrective action.

---

## 9. Shift notifications

| Event | Recipient | Channel | Priority | Notes |
| --- | --- | --- | --- | --- |
| shift_ready | Driver | in-app | medium | informative state |
| shift_online | Driver | in-app | low | confirmation only |
| shift_busy | Driver | none or passive in-app | low | usually reflected by active order UI |
| shift_ending_started | Driver | in-app | medium | warn about remaining steps |
| shift_close_blocked | Driver | Telegram + in-app blocker | high | unresolved order/trip sheet/etc |
| shift_closed | Driver | Telegram + in-app | medium | summary/confirmation |

---

## 10. Order notifications

| Event | Recipient | Channel | Priority | Notes |
| --- | --- | --- | --- | --- |
| order_offer_available | Driver | Telegram + in-app | high | should be actionable |
| order_accepted | Driver | Telegram + in-app | high | confirmation with next step |
| order_arriving | Driver | in-app | medium | often visible in active order screen |
| order_ontrip | Driver | in-app | medium | status confirmation |
| order_done | Driver | Telegram + in-app | medium | completion summary possible |
| order_canceled_before_accept | Driver | Telegram + in-app | medium | if previously visible/active |
| order_canceled_after_accept | Driver | Telegram + in-app | high | important working interruption |
| scheduled_order_reminder | Driver | Telegram + in-app | high | send ahead of scheduled time |

### Notes
- `order_offer_available` should have anti-spam controls if many offers arrive.
- `order_arriving` and `order_ontrip` can often remain in-app only if driver already controls those transitions.

---

## 11. Moderator/Admin notifications

| Event | Recipient | Channel | Priority | Notes |
| --- | --- | --- | --- | --- |
| profile_needs_review | Moderator/Admin | internal | high | moderation queue |
| document_needs_review | Moderator/Admin | internal | high | review queue |
| repeated_transition_errors | Moderator/Admin | internal | medium | potential bug or abuse |
| admin_override_performed | Moderator/Admin | internal | high | audit visibility |
| critical_driver_block | Moderator/Admin | internal | high | staff awareness |

---

## 12. Deduplication and cooldown rules

### 12.1. Deduplication key
Recommended dedupe key:
- `recipient_id + event_type + entity_id + state_version`

### 12.2. Cooldown candidates
Cooldown should be applied to events like:
- `document_expiring_soon`
- `eligibility_partially_ready`
- repeated `order_offer_available`
- repeated `shift_close_blocked`

### 12.3. Aggregation candidates
Can be aggregated:
- multiple expiring documents
- multiple missing readiness items
- multiple non-critical reminders in the same session

---

## 13. Fallback rules

- If Telegram delivery fails, critical and high events should still surface in-app.
- If in-app context is unavailable, Telegram remains the primary urgent fallback.
- Internal/audit events should not depend on user-facing channel success.

---

## 14. Backend event recommendations

Backend should emit canonical events such as:
- `profile_status_changed`
- `document_status_changed`
- `trip_sheet_status_changed`
- `eligibility_changed`
- `shift_status_changed`
- `order_status_changed`

Then notification routing layer decides:
- recipient
- channel
- priority
- text template
- dedupe policy

---

## 15. Related docs

- `docs/driver_status_contract.md`
- `docs/driver_permissions_matrix.md`
- `docs/driver_master_ux_map.md`
- `docs/driver_order_flow.md`
- `docs/driver_shift_flow.md`
- `docs/driver_ui_kit.md`

---

## 16. Next steps

После фиксации этой матрицы логично добавить:
- text template catalog
- notification event enums in backend code
- cooldown values per event
- retry/failure policy by channel
- QA checklist for notification delivery and dedupe
