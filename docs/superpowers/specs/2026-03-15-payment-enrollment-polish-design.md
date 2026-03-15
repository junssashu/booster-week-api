# Payment & Enrollment Polish — Design Spec

**Date:** 2026-03-15
**Status:** Approved
**Scope:** Backend (Django) + Web (Next.js) + Mobile (Flutter)

## Problem Statement

After deploying MoneyFusion production payments, several gaps prevent real-world usage:

1. **No enrollment UI on web** — `EnrollmentForm` component exists but is never used. Students cannot enroll in programs from the web app.
2. **Expired payments block retry** — Pending payments >15min stay `pending` in DB, causing 409 Conflict when students try to pay again.
3. **Flutter app ignores MoneyFusion redirect** — Uses polling-only flow; doesn't handle `paymentUrl` for production payments.
4. **No payment history** — Students cannot see their past payments.
5. **Generic confirmation page** — Doesn't show what was unlocked or provide next steps.
6. **No program discovery from dashboard** — Students must manually navigate to `/programmes`.

## Decisions Made

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Payment expiry timeout | 15 minutes | More aggressive than 30min, reduces user frustration |
| Enrollment UX | Quick-enroll dialog (minimal friction) | Just payment type + optional promo code, then straight to payment |
| Flutter MoneyFusion flow | In-app WebView | User stays in app, can detect return URL automatically |
| Payment history | Dedicated `/paiements` page | Full overview across all enrollments, with filters |
| Approach | Feature-by-feature (A) | Each feature shippable independently, clean dependency order |

## Feature 1: Auto-Expire Stale Pending Payments

### Backend Changes

**Setting:** Add `PAYMENT_EXPIRY_MINUTES` to `config/settings/base.py`:
```python
PAYMENT_EXPIRY_MINUTES = int(os.getenv('PAYMENT_EXPIRY_MINUTES', '15'))
```

**Eager check at initiation time** in `PaymentInitiateView.post()`:

Before raising 409 Conflict for an existing pending payment, check if it's older than `PAYMENT_EXPIRY_MINUTES`. If so, mark it `expired` and proceed with the new payment.

```python
from django.utils import timezone
from datetime import timedelta

cutoff = timezone.now() - timedelta(minutes=settings.PAYMENT_EXPIRY_MINUTES)

# Expire stale pending payments
Payment.objects.filter(
    enrollment=enrollment,
    status='pending',
    created_at__lt=cutoff
).update(status='expired')

# Now check for non-stale pending
if Payment.objects.filter(enrollment=enrollment, status='pending').exists():
    raise ConflictError('A payment is already pending for this enrollment.')
```

No cron job needed. Expiry is lazy — checked only when it matters.

**Also update `expires_at` in the initiate response** (views.py line 553) to use `PAYMENT_EXPIRY_MINUTES` instead of hardcoded 30 minutes. This keeps the client-facing expiry consistent with the backend auto-expiry.

### Files Affected
- `config/settings/base.py`
- `apps/enrollments/views.py` — `PaymentInitiateView.post()` (expiry check + `expires_at` response)
- `.env.example` — document `PAYMENT_EXPIRY_MINUTES`

## Feature 2: Web App Enrollment Flow (Quick Enroll)

### 2a. Conditional CTA on Program Detail Page

On `/programmes/[id]`, detect authentication state:
- **Not logged in:** "S'inscrire maintenant" → `/inscription` (existing)
- **Logged in, not enrolled:** "S'inscrire" → opens quick-enroll dialog
- **Logged in, already enrolled:** "Continuer la formation" → `/formations/[programId]`

Detection: Call `GET /enrollments` and filter client-side by `programId` (the endpoint doesn't support programId filtering, but enrollment count per user is low so client-side filtering is fine).

### 2b. Quick-Enroll Dialog

Lightweight modal component with:
- Program name + price summary
- Payment type toggle: "Paiement intégral" / "En 2 fois"
- Optional promo code input with "Valider" button
- Price recalculation when promo applied
- "Confirmer et payer" button (disable after first click to prevent double-submit):
  1. `POST /enrollments` with `{programId, paymentType, promoCode?}`
  2. Handle 409 Conflict gracefully (user already enrolled → redirect to formation)
  3. On success, redirect to `/paiement/[enrollmentId]`

### Files Affected

- `src/app/(public)/programmes/[id]/page.tsx` — conditional CTA
- New: `src/components/student/quick-enroll-dialog.tsx`

Note: The "browse programs" card on the dashboard is consolidated into Feature 6.

Note: The existing `src/components/student/enrollment-form.tsx` is unused and has a `valid`/`isValid` field name bug. It should be deleted as part of this feature — `quick-enroll-dialog.tsx` replaces it.

## Feature 3: Flutter MoneyFusion WebView

### 3a. Fix payment method string mismatch (prerequisite)

The Flutter app sends snake_case method strings (`orange_money`, `mtn_money`) but the backend expects camelCase (`orangeMoney`, `mtnMoney`). This is an existing bug that causes 400 errors on every Orange Money and MTN payment from the Flutter app.

Fix in `lib/features/payment/screens/payment_screen.dart` `_getMethodString()` to return camelCase values matching the backend serializer.

### 3b. WebView Payment Screen

When `initiatePayment()` returns a `paymentUrl`:
1. Navigate to a new `PaymentWebViewScreen`
2. Load MoneyFusion URL in `webview_flutter` WebView
3. Monitor URL changes via `NavigationDelegate`
4. When URL **contains** `boosterweekcenter.com/paiement/confirmation` (use `contains` check, not exact match — MoneyFusion may append extra query params):
   - Extract `token` parameter from URL
   - Close WebView
   - Call `GET /payments/verify?token=` to confirm
   - Show success/failure result
5. Handle loading errors gracefully (MoneyFusion page can be slow on mobile data in Côte d'Ivoire) — show loading spinner + timeout message

### 3c. Fallback

If no `paymentUrl` returned (dev mode), keep existing polling flow unchanged.

### Flow
```
initiatePayment() → has paymentUrl?
  ├── YES → push PaymentWebViewScreen(url)
  │         → intercept return_url redirect
  │         → extract token → pop WebView
  │         → verify payment → show result
  └── NO  → existing polling flow (dev mode)
```

### Files Affected
- `pubspec.yaml` — add `webview_flutter` dependency
- `lib/features/payment/screens/payment_screen.dart` — branch on `paymentUrl`
- New: `lib/features/payment/screens/payment_webview_screen.dart`
- `lib/core/providers/payment_provider.dart` — add `verifyPaymentByToken()` method
- `lib/core/services/payment_service.dart` — add `verifyPayment(token)` API call

## Feature 4: Payment History Page

### 4a. Backend — New Endpoint

`GET /payments/history`
- Returns all payments for the authenticated user across all enrollments
- Ordered by `created_at` descending
- Each payment includes: `id`, `amount`, `method`, `status`, `createdAt`, plus nested `enrollment.programName`, `enrollment.programImageUrl`, `enrollment.id`
- Optional query filters: `?status=completed`, `?method=orangeMoney`

### 4b. Web — `/paiements` Page

New page in student section:
- Filter chips: Tous / Complétés / Échoués / Expirés / En attente
- List/table: Date, Programme (with image), Montant, Méthode (icon), Statut (badge)
- Empty state: "Aucun paiement pour le moment"
- Add "Paiements" to sidebar nav before "Profil" (at `src/components/layouts/student-layout.tsx`)

### 4c. Flutter — Payment History Screen

Same as web:
- List view with program name, amount, method icon, status badge, date
- Filter chips at top
- Add "Paiements" to navigation drawer

### Files Affected
- `apps/enrollments/views.py` — new `PaymentHistoryView`
- `apps/enrollments/urls.py` — add `payments/history` route (**must be declared before** `payments/<str:payment_id>/status` to avoid URL pattern conflict)
- `apps/enrollments/serializers.py` — new `PaymentHistorySerializer`
- New: `src/app/(student)/paiements/page.tsx`
- Student sidebar component — add nav link
- New: `lib/features/payment/screens/payment_history_screen.dart`
- `lib/app/router.dart` — add route
- `lib/core/services/payment_service.dart` — add `getPaymentHistory()`

## Feature 5: Better Confirmation Page

### 5a. Backend — Enrich Verify Response

`GET /payments/verify?token=` currently returns `{status, paymentId}`.

Add: `programId`, `programName`, `enrollmentId`, `amountPaid`, `enrollmentPaymentStatus` (enrollment-level — named distinctly from the payment-level `status` already in the response).

Note: `enrollmentId` is already returned; the others are new. These fields are returned regardless of payment status (pending, completed, or failed) so the frontend always has context for display.

This avoids a second API call from the frontend.

### 5b. Web — Enhanced Success State

On success:
- Success animation (checkmark)
- Programme name and amount paid
- What was unlocked: "Vous avez maintenant accès au Degré 1: ..." (from enrollment detail)
- CTA: "Commencer la formation" → `/formations/[programId]`
- Secondary: "Voir mes paiements" → `/paiements`

### 5c. Web — Enhanced Failure State

- "Paiement échoué" with method + amount
- "Réessayer" → `/paiement/[enrollmentId]`
- "Contacter le support" secondary link

### 5d. Flutter — Same Improvements

Mirror the enriched success/failure screens in the Flutter result view.

### Files Affected
- `apps/enrollments/views.py` — enrich `PaymentVerifyView` response
- `src/app/(public)/paiement/confirmation/page.tsx` — enhanced UI
- `lib/features/payment/screens/payment_screen.dart` — enhanced result in Flutter

## Feature 6: Browse Programs from Student Dashboard

### 6a. Web — Dashboard Quick Action Card

Add "Découvrir les programmes" card on `/accueil` with explore/books icon, linking to `/programmes`. Same style as existing cards.

### 6b. Web — Sidebar Link

Add "Programmes" in student sidebar between "Formations" and "Progression", linking to `/programmes`.

### 6c. Flutter — Same Treatment

Add discovery card on home screen and ensure programs list is accessible from navigation.

### Files Affected
- `src/app/(student)/accueil/page.tsx` — quick action card
- Student sidebar/layout component — nav link
- `lib/features/home/screens/home_screen.dart` — card in Flutter

## Implementation Order

Features are ordered by dependency:

1. **Auto-expire payments** (backend only — unblocks retry)
2. **Enrollment flow** (web — biggest user-facing gap)
3. **Flutter MoneyFusion WebView** (Flutter — critical for mobile payments)
4. **Payment history page** (backend + web + Flutter)
5. **Better confirmation page** (web + Flutter)
6. **Browse programs from dashboard** (web + Flutter — trivial)

Each feature is independently deployable.
