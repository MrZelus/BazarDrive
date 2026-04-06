# BazarDrive MVP Roadmap

## Current MVP epics

- [#445 Driver Readiness Platform](https://github.com/MrZelus/BazarDrive/issues/445)
- [#460 Orders Marketplace Core](https://github.com/MrZelus/BazarDrive/issues/460)
- [#475 Feed Public Presence MVP](https://github.com/MrZelus/BazarDrive/issues/475)

---

## Roadmap table

| Epic | Issue | Priority | Depends on | Purpose | Suggested start |
|---|---:|---|---|---|---|
| Driver Readiness | #452 | P0 | none | readiness API and blocking reasons | first |
| Driver Readiness | #449 | P1 | #452 | hero/profile readiness summary UI | after #452 |
| Driver Readiness | #450 | P1 | #452 | checklist + navigation to missing fields | after #452 |
| Driver Readiness | #451 | P1 | #452 | documents section + active waybill priority | after #452 |
| Driver Readiness | #453 | P1 | #451 | document lifecycle enums and rules | together with #451 |
| Driver Readiness | #454 | P2 | #452 | Taxi / IP business profile | after core readiness |
| Driver Readiness | #455 | P2 | #449, #450, #451 | human-friendly states | after primary UI |
| Driver Readiness | #456 | P2 | #452, #453 | smoke + contract tests | after contracts |

| Epic | Issue | Priority | Depends on | Purpose | Suggested start |
|---|---:|---|---|---|---|
| Orders Core | #470 | P0 | none | orders API contracts and active trip summary | first |
| Orders Core | #465 | P1 | #470 | passenger order form and confirmation | after #470 |
| Orders Core | #466 | P1 | #470 | driver open orders list and cards | after #470 |
| Orders Core | #467 | P1 | #470 | driver accept order flow with race protection | after #470 |
| Orders Core | #468 | P1 | #470 | order lifecycle state machine | after #470 |
| Orders Core | #469 | P1 | #468 | active trip card with next-action UX | after lifecycle |
| Orders Core | #471 | P2 | #465, #466, #469 | human-friendly states for orders | after main UX |
| Orders Core | #472 | P2 | #470, #468 | smoke + contract tests | after contracts and lifecycle |

| Epic | Issue | Priority | Depends on | Purpose | Suggested start |
|---|---:|---|---|---|---|
| Feed Public Presence | #484 | P0 | none | feed publish/read contracts | first |
| Feed Public Presence | #480 | P1 | #484 | post composer + publish CTA | after #484 |
| Feed Public Presence | #481 | P1 | #484 | approved feed post cards | after #484 |
| Feed Public Presence | #482 | P1 | #484 | one-image media attachment | after #484 |
| Feed Public Presence | #483 | P1 | #484 | moderation-aware publish states | after #484 |
| Feed Public Presence | #485 | P2 | #481 | feed shell loading/empty/error states | after post cards |
| Feed Public Presence | #486 | P2 | #484 | smoke + contract tests | after contracts |

---

## Recommended implementation waves

### Wave 1: contracts and platform rails
- #452 Readiness summary API and blocking reasons contract
- #470 Orders API contracts and active trip summary
- #484 Feed publish/read contracts and media payload rules

### Wave 2: primary user flows
- #449 Refactor driver profile hero and readiness summary
- #465 Implement passenger order form and confirmation flow
- #480 Build feed post composer and publish CTA flow

### Wave 3: supporting operational UX
- #450 Implement driver checklist with blocking navigation
- #466 Build driver open orders list and order cards
- #481 Build approved feed post cards with safe rendering

### Wave 4: functional depth
- #451 Rework documents section with active waybill priority
- #467 Implement driver accept order flow with race protection
- #482 Add one-image media attachment for feed posts
- #483 Add moderation-aware publish states and copy

### Wave 5: domain stabilization
- #453 Normalize driver document lifecycle enums
- #454 Implement Taxi / IP business profile section
- #468 Implement order lifecycle state machine
- #469 Build active trip card with next-action UX
- #485 Add loading, empty, and error states for feed shell

### Wave 6: quality and regression safety
- #455 Add human-friendly empty, loading, pending, and error states
- #456 Cover driver onboarding with smoke and contract tests
- #471 Add human-friendly loading, empty, and error states for orders
- #472 Cover orders core with smoke and contract tests
- #486 Cover feed public presence with smoke and contract tests

---

## Suggested ownership split

### Backend
- #452
- #470
- #484
- #468
- #453

### Frontend
- #449
- #450
- #451
- #454
- #465
- #466
- #469
- #480
- #481
- #482
- #483
- #485

### QA / stabilization
- #455
- #456
- #471
- #472
- #486

---

## MVP checkpoint definition

The MVP can be considered structurally usable when all of the following are working:

### Driver readiness
- driver can complete profile onboarding
- readiness is computed on the server
- missing fields and documents are visible and actionable

### Orders core
- passenger can create an order
- driver can see open orders
- driver can accept an order
- lifecycle transitions are enforced consistently

### Feed public presence
- user can publish a post
- approved posts render in the feed
- image attachment works for a single image
- moderation-aware publish states are shown clearly

---

## Immediate next actions

1. Start with:
   - #452
   - #470
   - #484

2. Then build first visible UX:
   - #449
   - #465
   - #480

3. Then complete the first usable flows:
   - #450
   - #451
   - #466
   - #467
   - #481
   - #482
   - #483

4. After that, stabilize with:
   - #453
   - #454
   - #468
   - #469
   - #455
   - #456
   - #471
   - #472
   - #485
   - #486
