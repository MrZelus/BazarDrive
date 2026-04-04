# Guest Feed Privacy & Driver Profile Separation

## Summary

In the current version of `public/guest_feed.html`, the guest feed contains a **driver profile** block intended for authenticated or order-bound scenarios. For an unauthenticated guest, this is a privacy and architecture problem:

- public feed should not expose driver-specific personal data;
- guest users do not yet have a valid driver interaction context;
- driver actions in guest mode create broken or misleading UX.

This should be treated as a **privacy-by-design**, **data minimization**, and **guest-flow separation** task.

---

## Problem

### Business / UX
- Guest users should see a public feed, onboarding, and registration/login CTAs.
- Driver profile data should only appear:
  - after authentication, or
  - inside an active / assigned taxi order flow.
- Showing a driver profile before that creates a confusing mental model and weakens trust.

### Privacy / Security
- Guest pages must not display personal driver data such as:
  - full name,
  - phone,
  - vehicle identifiers,
  - documents,
  - compliance or payouts status.
- Driver-only blocks in public feed contradict privacy-by-default and least-data principles.

---

## Goal

Separate **guest feed** and **driver profile** scenarios so that:

1. guest feed contains only public-safe content;
2. driver profile is rendered only in authenticated or active-order contexts;
3. guest CTAs lead to registration/login/onboarding rather than inaccessible driver actions;
4. QA regression coverage prevents this coupling from returning.

---

## Scope

### 1. Remove driver profile from guest mode
- Remove or fully hide the `Профиль водителя` block from `public/guest_feed.html` in guest mode.
- Remove or hide related driver-only strings and DOM sections, including:
  - `Профиль водителя`
  - `Документы водителя`
  - `driverAddDocumentBtn`
  - `driverOverviewDocuments`
- Ensure that guest flow does not render driver compliance, driver docs, or payouts content.

### 2. Introduce marketing-safe driver showcase (optional)
If product still needs a promotional driver card in guest feed:

- use anonymized data only, such as:
  - `Водитель А.`
  - `Стаж 5 лет`
  - `Рейтинг 4.9`
  - `Оплата: Наличные`
- use approved static assets or default avatars;
- do not show real phone, real FIO, real car number, documents, compliance details.

### 3. Fix guest CTA behavior
- Any guest-visible CTA resembling driver interaction must not execute real driver actions.
- Buttons such as:
  - `Позвонить`
  - `Чат`
  - `Связаться`
  - `Заказать поездку`
  must redirect to:
  - registration,
  - authentication,
  - or onboarding.

### 4. Placeholder / empty-state behavior
- If driver-specific data is unavailable in guest mode:
  - either hide the block entirely,
  - or replace it with a placeholder:
    - `Авторизуйтесь, чтобы увидеть профиль водителя и детали поездки`.
- No empty template placeholders, broken IDs, or dead controls should remain in guest markup.

### 5. Mobile / layout QA
- Verify that guest blocks do not overlap sticky actions or bottom navigation.
- Ensure guest CTA remains visible and tappable on mobile.
- Prevent visual blending of guest-feed and driver-profile sections.

---

## QA requirements

### Regression checks
Add coverage ensuring that in guest mode:

- `guest_feed.html` does **not** expose driver-only content before auth;
- no real driver personal data is rendered in public feed;
- no driver-only payouts text is shown in guest profile/feed context, including:
  - `Доход за день`
  - `Открыть выплаты`
- guest CTA opens registration/login rather than protected actions.

### Suggested tests
- Add a regression test similar to `test_driver_tab_content_regression.py`, but for guest mode.
- Validate absence of driver-only DOM blocks in guest feed.
- Validate that guest CTA routes to auth/onboarding.
- Add mobile smoke check for guest layout and sticky CTA behavior.

---

## Suggested implementation notes

- Introduce explicit screen/context split:
  - `guest_public_feed`
  - `authenticated_profile`
  - `active_order_driver_card`
- Guard driver DOM rendering behind auth/order-state checks.
- Keep public feed components privacy-safe by default.

---

## Definition of done

- Guest feed no longer contains driver-only profile data or controls.
- Driver profile appears only in authenticated or active-order contexts.
- Guest-visible CTAs are valid and lead to the next allowed step.
- Regression tests cover privacy, DOM separation, and CTA behavior.
- Mobile layout remains stable.
