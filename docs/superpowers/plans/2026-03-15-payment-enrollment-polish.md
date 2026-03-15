# Payment & Enrollment Polish Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 3 critical blockers (payment retry, web enrollment, Flutter MoneyFusion redirect) and add 3 UX improvements (payment history, better confirmation, program discovery) across backend, web, and Flutter.

**Architecture:** Feature-by-feature approach — each feature is built end-to-end (backend → web → Flutter) and independently deployable. Backend is Django REST Framework, web is Next.js 16, mobile is Flutter with Riverpod.

**Tech Stack:** Python/Django, TypeScript/Next.js, Dart/Flutter, PostgreSQL, MoneyFusion payment gateway

**Spec:** `docs/superpowers/specs/2026-03-15-payment-enrollment-polish-design.md`

---

## Chunk 1: Auto-Expire Payments + Web Enrollment Flow

### Task 1: Auto-Expire Stale Pending Payments (Backend)

**Files:**
- Modify: `config/settings/base.py:140-144`
- Modify: `apps/enrollments/views.py:525-529` (pending check) and `:553` (expires_at)
- Modify: `.env.example`

- [ ] **Step 1: Add PAYMENT_EXPIRY_MINUTES setting**

In `config/settings/base.py`, after line 143 (`MONEYFUSION_DEV_MODE`), add:

```python
PAYMENT_EXPIRY_MINUTES = int(os.getenv('PAYMENT_EXPIRY_MINUTES', '15'))
```

- [ ] **Step 2: Add PAYMENT_EXPIRY_MINUTES to .env.example**

Add under the MoneyFusion section:

```
PAYMENT_EXPIRY_MINUTES=15
```

- [ ] **Step 3: Update PaymentInitiateView to auto-expire stale payments**

In `apps/enrollments/views.py`, replace the pending payment check at lines 525-529:

```python
# OLD:
pending = Payment.objects.filter(
    enrollment=enrollment, status='pending'
).exists()
if pending:
    raise ConflictError('A payment is already pending for this enrollment.')
```

With:

```python
# Auto-expire stale pending payments
cutoff = timezone.now() - timedelta(minutes=settings.PAYMENT_EXPIRY_MINUTES)
Payment.objects.filter(
    enrollment=enrollment,
    status='pending',
    created_at__lt=cutoff,
).update(status='expired')

# Check for non-stale pending payments
if Payment.objects.filter(enrollment=enrollment, status='pending').exists():
    raise ConflictError('A payment is already pending for this enrollment.')
```

Ensure `from datetime import timedelta` is imported at the top of the file (it should already be there from `_complete_payment`).

- [ ] **Step 4: Update expires_at to use PAYMENT_EXPIRY_MINUTES**

In `apps/enrollments/views.py`, replace line 553:

```python
# OLD:
expires_at = timezone.now() + timedelta(minutes=30)
```

With:

```python
expires_at = timezone.now() + timedelta(minutes=settings.PAYMENT_EXPIRY_MINUTES)
```

- [ ] **Step 5: Test locally**

```bash
cd /Users/joetec/Documents/coding/brad_projects/booster_week_backend
python manage.py check
```

Expected: System check identified no issues.

- [ ] **Step 6: Commit**

```bash
git add config/settings/base.py apps/enrollments/views.py .env.example
git commit -m "feat: auto-expire stale pending payments after 15 minutes"
```

---

### Task 2: Quick-Enroll Dialog Component (Web)

**Files:**
- Create: `booster_week_web/src/components/student/quick-enroll-dialog.tsx`
- Delete: `booster_week_web/src/components/student/enrollment-form.tsx`

- [ ] **Step 1: Create the quick-enroll dialog component**

Create `src/components/student/quick-enroll-dialog.tsx`:

```tsx
"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

interface QuickEnrollDialogProps {
  programId: string;
  programName: string;
  price: number;
  isOpen: boolean;
  onClose: () => void;
}

export function QuickEnrollDialog({
  programId,
  programName,
  price,
  isOpen,
  onClose,
}: QuickEnrollDialogProps) {
  const router = useRouter();
  const [paymentType, setPaymentType] = useState<"full" | "installment">("full");
  const [promoCode, setPromoCode] = useState("");
  const [promoResult, setPromoResult] = useState<{
    valid: boolean;
    discountPercent: number;
  } | null>(null);
  const [validatingPromo, setValidatingPromo] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const discountedPrice = promoResult?.valid
    ? Math.ceil(price * (1 - promoResult.discountPercent / 100))
    : price;

  const displayAmount =
    paymentType === "installment"
      ? Math.ceil(discountedPrice / 2)
      : discountedPrice;

  const handleValidatePromo = async () => {
    if (!promoCode.trim()) return;
    setValidatingPromo(true);
    try {
      const result = await api.post<{ valid: boolean; discountPercent: number }>(
        "/promo-codes/validate",
        { code: promoCode.trim() }
      );
      setPromoResult(result);
      if (result.valid) {
        toast.success(`Code promo appliqué: -${result.discountPercent}%`);
      } else {
        toast.error("Code promo invalide");
      }
    } catch {
      toast.error("Erreur de validation du code promo");
    } finally {
      setValidatingPromo(false);
    }
  };

  const handleEnroll = async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      const result = await api.post<{ data: { id: string } }>("/enrollments", {
        programId,
        paymentType,
        ...(promoCode.trim() && promoResult?.valid ? { promoCode: promoCode.trim() } : {}),
      });
      toast.success("Inscription réussie !");
      router.push(`/paiement/${result.data.id}`);
    } catch (err: unknown) {
      const error = err as { status?: number };
      if (error.status === 409) {
        toast.info("Vous êtes déjà inscrit à ce programme");
        router.push(`/formations/${programId}`);
      } else {
        toast.error("Erreur lors de l'inscription");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-neutral-900 rounded-2xl p-6 w-full max-w-md mx-4 shadow-xl">
        <h2 className="text-xl font-bold mb-1">S&apos;inscrire</h2>
        <p className="text-sm text-muted-foreground mb-4">{programName}</p>

        {/* Payment Type */}
        <div className="space-y-2 mb-4">
          <label className="text-sm font-medium">Type de paiement</label>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => setPaymentType("full")}
              className={`p-3 rounded-xl border text-sm text-center transition ${
                paymentType === "full"
                  ? "border-orange-500 bg-orange-50 dark:bg-orange-950 text-orange-700"
                  : "border-neutral-200 dark:border-neutral-700"
              }`}
            >
              <div className="font-medium">Paiement intégral</div>
              <div className="text-xs text-muted-foreground">
                {discountedPrice.toLocaleString()} XOF
              </div>
            </button>
            <button
              onClick={() => setPaymentType("installment")}
              className={`p-3 rounded-xl border text-sm text-center transition ${
                paymentType === "installment"
                  ? "border-orange-500 bg-orange-50 dark:bg-orange-950 text-orange-700"
                  : "border-neutral-200 dark:border-neutral-700"
              }`}
            >
              <div className="font-medium">En 2 fois</div>
              <div className="text-xs text-muted-foreground">
                {Math.ceil(discountedPrice / 2).toLocaleString()} XOF / fois
              </div>
            </button>
          </div>
        </div>

        {/* Promo Code */}
        <div className="mb-4">
          <label className="text-sm font-medium">Code promo (optionnel)</label>
          <div className="flex gap-2 mt-1">
            <input
              type="text"
              value={promoCode}
              onChange={(e) => {
                setPromoCode(e.target.value);
                setPromoResult(null);
              }}
              placeholder="Entrez votre code"
              className="flex-1 px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-transparent text-sm"
            />
            <button
              onClick={handleValidatePromo}
              disabled={!promoCode.trim() || validatingPromo}
              className="px-4 py-2 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-sm font-medium disabled:opacity-50"
            >
              {validatingPromo ? "..." : "Valider"}
            </button>
          </div>
          {promoResult?.valid && (
            <p className="text-xs text-green-600 mt-1">
              -{promoResult.discountPercent}% appliqué
            </p>
          )}
        </div>

        {/* Summary */}
        <div className="bg-orange-50 dark:bg-orange-950/30 rounded-xl p-3 mb-4 text-center">
          <p className="text-xs text-muted-foreground">Montant à payer</p>
          <p className="text-2xl font-bold text-orange-600">
            {displayAmount.toLocaleString()} XOF
          </p>
          {paymentType === "installment" && (
            <p className="text-xs text-muted-foreground">1ère tranche sur 2</p>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 rounded-xl border border-neutral-200 dark:border-neutral-700 text-sm font-medium"
          >
            Annuler
          </button>
          <button
            onClick={handleEnroll}
            disabled={submitting}
            className="flex-1 px-4 py-3 rounded-xl bg-orange-500 text-white text-sm font-medium disabled:opacity-50"
          >
            {submitting ? "Inscription..." : "Confirmer et payer"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Delete the unused enrollment-form.tsx**

```bash
rm booster_week_web/src/components/student/enrollment-form.tsx
```

- [ ] **Step 3: Commit**

```bash
cd /Users/joetec/Documents/coding/brad_projects/booster_week_web
git add src/components/student/quick-enroll-dialog.tsx
git rm src/components/student/enrollment-form.tsx
git commit -m "feat: add quick-enroll dialog, remove unused enrollment form"
```

---

### Task 3: Wire Quick-Enroll into Program Detail Page (Web)

**Files:**
- Modify: `booster_week_web/src/app/(public)/programmes/[id]/page.tsx:134-143`

- [ ] **Step 1: Update program detail page with conditional CTA**

Replace the entire file `src/app/(public)/programmes/[id]/page.tsx` to add client-side enrollment detection. The page is currently server-rendered, so we need to extract the CTA into a client component.

Create a new client component `src/app/(public)/programmes/[id]/program-cta.tsx`:

```tsx
"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { QuickEnrollDialog } from "@/components/student/quick-enroll-dialog";
import type { Enrollment } from "@/types";

interface ProgramCTAProps {
  programId: string;
  programName: string;
  price: number;
}

export function ProgramCTA({ programId, programName, price }: ProgramCTAProps) {
  const [state, setState] = useState<"loading" | "guest" | "not-enrolled" | "enrolled">("loading");
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    const checkEnrollment = async () => {
      try {
        const result = await api.get<{ data: Enrollment[] }>("/enrollments");
        const enrolled = result.data.some((e) => e.programId === programId);
        setState(enrolled ? "enrolled" : "not-enrolled");
      } catch {
        // Not authenticated or error — treat as guest
        setState("guest");
      }
    };
    checkEnrollment();
  }, [programId]);

  if (state === "loading") return null;

  if (state === "enrolled") {
    return (
      <Link
        href={`/formations/${programId}`}
        className="inline-flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-8 py-4 rounded-full text-lg font-semibold transition-colors"
      >
        Continuer la formation
        <ArrowRight className="w-5 h-5" />
      </Link>
    );
  }

  if (state === "not-enrolled") {
    return (
      <>
        <button
          onClick={() => setDialogOpen(true)}
          className="inline-flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-8 py-4 rounded-full text-lg font-semibold transition-colors"
        >
          S&apos;inscrire au programme
          <ArrowRight className="w-5 h-5" />
        </button>
        <QuickEnrollDialog
          programId={programId}
          programName={programName}
          price={price}
          isOpen={dialogOpen}
          onClose={() => setDialogOpen(false)}
        />
      </>
    );
  }

  // Guest — go to registration
  return (
    <Link
      href="/inscription"
      className="inline-flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-8 py-4 rounded-full text-lg font-semibold transition-colors"
    >
      S&apos;inscrire maintenant
      <ArrowRight className="w-5 h-5" />
    </Link>
  );
}
```

- [ ] **Step 2: Update the program detail page to use ProgramCTA**

In `src/app/(public)/programmes/[id]/page.tsx`, replace the CTA section (lines 134-143):

```tsx
// OLD (lines 134-143):
<Link href="/inscription" className="...">
  S'inscrire maintenant
  <ArrowRight />
</Link>
```

With import at the top:
```tsx
import { ProgramCTA } from "./program-cta";
```

And in the JSX, replace the Link CTA with:
```tsx
<ProgramCTA
  programId={program.id}
  programName={program.name}
  price={program.price}
/>
```

- [ ] **Step 3: Verify the build**

```bash
cd /Users/joetec/Documents/coding/brad_projects/booster_week_web
npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 4: Commit**

```bash
git add src/app/\(public\)/programmes/\[id\]/program-cta.tsx src/app/\(public\)/programmes/\[id\]/page.tsx
git commit -m "feat: add conditional enrollment CTA on program detail page"
```

---

### Task 4: Deploy Feature 1 + 2 to VPS

**Files:** None (deployment only)

- [ ] **Step 1: Deploy backend**

```bash
rsync -avz /Users/joetec/Documents/coding/brad_projects/booster_week_backend/ bib-vps:/home/ubuntu/apps/booster-week-api/ --exclude='.git' --exclude='__pycache__' --exclude='.env' --exclude='db.sqlite3'
ssh bib-vps "cd /home/ubuntu/apps/booster-week-api && docker compose up -d --build web"
```

- [ ] **Step 2: Deploy frontend**

```bash
rsync -avz /Users/joetec/Documents/coding/brad_projects/booster_week_web/ bib-vps:/home/ubuntu/apps/booster-week-web/ --exclude='.git' --exclude='node_modules' --exclude='.next' --exclude='.env'
ssh bib-vps "cd /home/ubuntu/apps/booster-week-web && docker compose up -d --build"
```

- [ ] **Step 3: Verify**

```bash
curl -s https://api.boosterweekcenter.com/api/v1/payments/initiate -X POST -H 'Content-Type: application/json' | python3 -c "import sys,json; print(json.load(sys.stdin))" 2>/dev/null
curl -s -o /dev/null -w '%{http_code}' https://boosterweekcenter.com
```

---

## Chunk 2: Flutter MoneyFusion WebView

### Task 5: Fix Flutter Payment Method String Mismatch

**Files:**
- Modify: `booster_week/lib/features/payment/screens/payment_screen.dart:55-64`

- [ ] **Step 1: Fix _getMethodString() to return camelCase**

In `lib/features/payment/screens/payment_screen.dart`, replace lines 55-64:

```dart
// OLD:
String _getMethodString(PaymentMethod method) {
  switch (method) {
    case PaymentMethod.orangeMoney:
      return 'orange_money';
    case PaymentMethod.mtnMoney:
      return 'mtn_money';
    case PaymentMethod.wave:
      return 'wave';
  }
}
```

With:

```dart
String _getMethodString(PaymentMethod method) {
  switch (method) {
    case PaymentMethod.orangeMoney:
      return 'orangeMoney';
    case PaymentMethod.mtnMoney:
      return 'mtnMoney';
    case PaymentMethod.wave:
      return 'wave';
  }
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/joetec/Documents/coding/brad_projects/booster_week
git add lib/features/payment/screens/payment_screen.dart
git commit -m "fix: use camelCase payment method strings matching backend API"
```

---

### Task 6: Add Payment Verify Service Method (Flutter)

**Files:**
- Modify: `booster_week/lib/core/services/payment_service.dart`

- [ ] **Step 1: Add verifyPayment method**

In `lib/core/services/payment_service.dart`, after the `getEnrollmentPayments` method (after line 47), add:

```dart
Future<Map<String, dynamic>> verifyPayment(String token) async {
  final response = await ApiConfig.dio.get('/payments/verify', queryParameters: {'token': token});
  return response.data['data'];
}
```

- [ ] **Step 2: Commit**

```bash
git add lib/core/services/payment_service.dart
git commit -m "feat: add verifyPayment service method for MoneyFusion return flow"
```

---

### Task 7: Create PaymentWebViewScreen (Flutter)

**Files:**
- Create: `booster_week/lib/features/payment/screens/payment_webview_screen.dart`
- Modify: `booster_week/pubspec.yaml` — add `webview_flutter`

- [ ] **Step 1: Add webview_flutter dependency**

```bash
cd /Users/joetec/Documents/coding/brad_projects/booster_week
flutter pub add webview_flutter
```

- [ ] **Step 2: Create the WebView screen**

Create `lib/features/payment/screens/payment_webview_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class PaymentWebViewScreen extends StatefulWidget {
  final String paymentUrl;
  final String returnUrlPattern;

  const PaymentWebViewScreen({
    super.key,
    required this.paymentUrl,
    this.returnUrlPattern = 'boosterweekcenter.com/paiement/confirmation',
  });

  @override
  State<PaymentWebViewScreen> createState() => _PaymentWebViewScreenState();
}

class _PaymentWebViewScreenState extends State<PaymentWebViewScreen> {
  late final WebViewController _controller;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) => setState(() => _isLoading = true),
          onPageFinished: (_) => setState(() => _isLoading = false),
          onNavigationRequest: (request) {
            if (request.url.contains(widget.returnUrlPattern)) {
              final uri = Uri.parse(request.url);
              final token = uri.queryParameters['token'];
              Navigator.of(context).pop(token);
              return NavigationDecision.prevent;
            }
            return NavigationDecision.navigate;
          },
          onWebResourceError: (error) {
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Erreur de chargement: ${error.description}'),
                  action: SnackBarAction(
                    label: 'Réessayer',
                    onPressed: () => _controller.reload(),
                  ),
                ),
              );
            }
          },
        ),
      )
      ..loadRequest(Uri.parse(widget.paymentUrl));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Paiement MoneyFusion'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(null),
        ),
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_isLoading)
            const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Chargement de la page de paiement...'),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add pubspec.yaml pubspec.lock lib/features/payment/screens/payment_webview_screen.dart
git commit -m "feat: add PaymentWebViewScreen for MoneyFusion in-app payments"
```

---

### Task 8: Wire WebView into Payment Screen (Flutter)

**Files:**
- Modify: `booster_week/lib/features/payment/screens/payment_screen.dart:89-155`
- Modify: `booster_week/lib/core/providers/payment_provider.dart`

- [ ] **Step 1: Add verifyPaymentByToken to PaymentNotifier**

In `lib/core/providers/payment_provider.dart`, add after the `devSimulatePayment` method (after line 148):

```dart
Future<String> verifyPaymentByToken(String token) async {
  state = state.copyWith(isProcessing: true, statusMessage: 'Vérification du paiement...');
  try {
    final result = await PaymentService().verifyPayment(token);
    final status = result['status'] as String;
    state = state.copyWith(
      isProcessing: false,
      lastResponse: result,
      statusMessage: status == 'completed' ? 'Paiement réussi !' : 'Paiement échoué',
    );
    return status;
  } catch (e) {
    state = state.copyWith(isProcessing: false, error: e.toString());
    return 'failed';
  }
}
```

- [ ] **Step 2: Update _processPayment in payment_screen.dart**

In `lib/features/payment/screens/payment_screen.dart`, in the `_processPayment` method (around line 89-155), after the `initiatePayment` call succeeds and you get the response, add a check for `paymentUrl`:

After the line that extracts `paymentId` from response (around line 109), add:

```dart
final paymentUrl = response['paymentUrl'] as String?;

if (paymentUrl != null && paymentUrl.isNotEmpty) {
  // Production mode: open MoneyFusion WebView
  if (!mounted) return;
  final token = await Navigator.of(context).push<String?>(
    MaterialPageRoute(
      builder: (_) => PaymentWebViewScreen(paymentUrl: paymentUrl),
    ),
  );

  if (token != null && token.isNotEmpty) {
    // User completed on MoneyFusion — verify
    final status = await ref.read(paymentProvider.notifier).verifyPaymentByToken(token);
    if (status == 'completed') {
      ref.read(enrollmentProvider.notifier).refreshEnrollments();
    }
    setState(() {
      _currentStep = 3; // Show result
    });
  } else {
    // User cancelled or closed WebView
    setState(() {
      _paymentStatus = 'cancelled';
      _currentStep = 3;
    });
  }
  return;
}

// Dev mode fallback: existing polling flow continues below
```

Add the import at the top of the file:

```dart
import 'package:booster_week/features/payment/screens/payment_webview_screen.dart';
```

- [ ] **Step 3: Build and verify**

```bash
cd /Users/joetec/Documents/coding/brad_projects/booster_week
flutter build apk --debug
```

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add lib/features/payment/screens/payment_screen.dart lib/core/providers/payment_provider.dart
git commit -m "feat: integrate MoneyFusion WebView into payment flow"
```

---

## Chunk 3: Payment History + Better Confirmation + Browse Programs

### Task 9: Payment History Backend Endpoint

**Files:**
- Modify: `booster_week_backend/apps/enrollments/views.py`
- Modify: `booster_week_backend/apps/enrollments/urls.py:9-13`
- Modify: `booster_week_backend/apps/enrollments/serializers.py`

- [ ] **Step 1: Add PaymentHistorySerializer**

In `apps/enrollments/serializers.py`, after `PaymentStatusSerializer` (after line 111), add:

```python
class PaymentHistorySerializer(serializers.Serializer):
    id = serializers.CharField()
    amount = serializers.IntegerField()
    method = serializers.CharField()
    status = serializers.CharField()
    date = serializers.DateTimeField(source='created_at')
    transactionRef = serializers.CharField(source='mf_transaction_id', default='')
    enrollmentId = serializers.CharField(source='enrollment_id')
    programName = serializers.SerializerMethodField()
    programImageUrl = serializers.SerializerMethodField()

    def get_programName(self, obj):
        return obj.enrollment.program.name if obj.enrollment and obj.enrollment.program else ''

    def get_programImageUrl(self, obj):
        return obj.enrollment.program.image_url if obj.enrollment and obj.enrollment.program else ''
```

- [ ] **Step 2: Add PaymentHistoryView**

In `apps/enrollments/views.py`, after `PaymentStatusView` (after the class that ends around line 598), add:

```python
class PaymentHistoryView(APIView):
    """List all payments for the authenticated user across all enrollments."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(
            enrollment__user=request.user
        ).select_related(
            'enrollment', 'enrollment__program'
        ).order_by('-created_at')

        # Optional filters
        status = request.query_params.get('status')
        if status:
            payments = payments.filter(status=status)
        method = request.query_params.get('method')
        if method:
            payments = payments.filter(method=method)

        serializer = PaymentHistorySerializer(payments, many=True)
        return Response({'data': serializer.data})
```

Import `PaymentHistorySerializer` in the imports section at the top of views.py.

- [ ] **Step 3: Add URL route — BEFORE the payment_id pattern**

In `apps/enrollments/urls.py`, add `payments/history` BEFORE `payments/<str:payment_id>/status` (before line 12):

```python
path('payments/history', views.PaymentHistoryView.as_view(), name='payment-history'),
```

- [ ] **Step 4: Test locally**

```bash
cd /Users/joetec/Documents/coding/brad_projects/booster_week_backend
python manage.py check
```

- [ ] **Step 5: Commit**

```bash
git add apps/enrollments/views.py apps/enrollments/urls.py apps/enrollments/serializers.py
git commit -m "feat: add GET /payments/history endpoint for payment history"
```

---

### Task 10: Enrich Payment Verify Response (Backend)

**Files:**
- Modify: `booster_week_backend/apps/enrollments/views.py:671-678`

- [ ] **Step 1: Update PaymentVerifyView response**

In `apps/enrollments/views.py`, replace the response dict at lines 671-678:

```python
# OLD:
return Response({
    'data': {
        'status': payment.status,
        'paymentId': payment.id,
        'amount': payment.amount,
        'enrollmentId': payment.enrollment_id,
    }
})
```

With:

```python
enrollment = payment.enrollment
program = enrollment.program if enrollment else None
return Response({
    'data': {
        'status': payment.status,
        'paymentId': payment.id,
        'amount': payment.amount,
        'enrollmentId': payment.enrollment_id,
        'programId': program.id if program else '',
        'programName': program.name if program else '',
        'enrollmentPaymentStatus': enrollment.payment_status if enrollment else '',
    }
})
```

- [ ] **Step 2: Commit**

```bash
git add apps/enrollments/views.py
git commit -m "feat: enrich payment verify response with program and enrollment info"
```

---

### Task 11: Payment History Page (Web)

**Files:**
- Create: `booster_week_web/src/app/(student)/paiements/page.tsx`
- Modify: `booster_week_web/src/components/layouts/student-layout.tsx:37-44`

- [ ] **Step 1: Create the payment history page**

Create `src/app/(student)/paiements/page.tsx`:

```tsx
"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { CreditCard, Smartphone } from "lucide-react";

interface PaymentHistoryItem {
  id: string;
  amount: number;
  method: string;
  status: string;
  date: string;
  programName: string;
  programImageUrl: string;
  enrollmentId: string;
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  completed: { label: "Complété", color: "bg-green-100 text-green-700" },
  pending: { label: "En attente", color: "bg-yellow-100 text-yellow-700" },
  failed: { label: "Échoué", color: "bg-red-100 text-red-700" },
  expired: { label: "Expiré", color: "bg-neutral-100 text-neutral-500" },
};

const METHOD_LABELS: Record<string, string> = {
  orangeMoney: "Orange Money",
  mtnMoney: "MTN Money",
  wave: "Wave",
};

const FILTERS = [
  { value: "", label: "Tous" },
  { value: "completed", label: "Complétés" },
  { value: "failed", label: "Échoués" },
  { value: "expired", label: "Expirés" },
  { value: "pending", label: "En attente" },
];

export default function PaymentHistoryPage() {
  const [payments, setPayments] = useState<PaymentHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    const fetchPayments = async () => {
      setLoading(true);
      try {
        const params = filter ? `?status=${filter}` : "";
        const result = await api.get<{ data: PaymentHistoryItem[] }>(
          `/payments/history${params}`
        );
        setPayments(result.data);
      } catch {
        setPayments([]);
      } finally {
        setLoading(false);
      }
    };
    fetchPayments();
  }, [filter]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Paiements</h1>

      {/* Filter chips */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition ${
              filter === f.value
                ? "bg-orange-500 text-white"
                : "bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Payment list */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-neutral-100 dark:bg-neutral-800 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : payments.length === 0 ? (
        <div className="text-center py-12">
          <CreditCard className="w-12 h-12 mx-auto text-neutral-300 mb-4" />
          <p className="text-neutral-500">Aucun paiement pour le moment</p>
        </div>
      ) : (
        <div className="space-y-3">
          {payments.map((p) => {
            const statusInfo = STATUS_LABELS[p.status] || STATUS_LABELS.pending;
            return (
              <div
                key={p.id}
                className="flex items-center gap-4 p-4 bg-white dark:bg-neutral-900 rounded-xl border border-neutral-100 dark:border-neutral-800"
              >
                {p.programImageUrl ? (
                  <img
                    src={p.programImageUrl}
                    alt=""
                    className="w-12 h-12 rounded-lg object-cover"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-lg bg-orange-100 flex items-center justify-center">
                    <Smartphone className="w-6 h-6 text-orange-500" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{p.programName}</p>
                  <p className="text-sm text-muted-foreground">
                    {METHOD_LABELS[p.method] || p.method} •{" "}
                    {new Date(p.date).toLocaleDateString("fr-FR", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-bold">{p.amount.toLocaleString()} XOF</p>
                  <span className={`text-xs px-2 py-1 rounded-full ${statusInfo.color}`}>
                    {statusInfo.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Add "Paiements" to sidebar nav**

In `src/components/layouts/student-layout.tsx`, in the sidebar links array (lines 37-44), add before the Profil entry:

```tsx
{ href: "/paiements", icon: CreditCard, label: "Paiements" },
```

And add `CreditCard` to the lucide-react import at the top.

- [ ] **Step 3: Build and verify**

```bash
cd /Users/joetec/Documents/coding/brad_projects/booster_week_web
npm run build
```

- [ ] **Step 4: Commit**

```bash
git add src/app/\(student\)/paiements/page.tsx src/components/layouts/student-layout.tsx
git commit -m "feat: add payment history page with filters"
```

---

### Task 12: Better Confirmation Page (Web)

**Files:**
- Modify: `booster_week_web/src/app/(public)/paiement/confirmation/page.tsx`

- [ ] **Step 1: Update the confirmation page**

Replace the `ConfirmationContent` component in `src/app/(public)/paiement/confirmation/page.tsx` to use the enriched verify response:

Update the `PaymentResult` type (lines 14-17):

```tsx
interface PaymentResult {
  status: string;
  paymentId: string;
  amount: number;
  enrollmentId: string;
  programId: string;
  programName: string;
  enrollmentPaymentStatus: string;
}
```

Update the verification call result type (around line 33-40) to use `PaymentResult` instead of just `{status, paymentId}`.

Update the **success state** (around lines 90-108) to show:

```tsx
{result?.status === "completed" && (
  <div className="text-center space-y-4">
    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
      <CheckCircle className="w-8 h-8 text-green-600" />
    </div>
    <h1 className="text-2xl font-bold">Paiement réussi !</h1>
    {result.programName && (
      <p className="text-muted-foreground">
        {result.enrollmentPaymentStatus === "completed"
          ? `Vous avez maintenant accès à "${result.programName}"`
          : `Paiement partiel reçu pour "${result.programName}"`}
      </p>
    )}
    <p className="text-lg font-semibold text-orange-600">
      {result.amount?.toLocaleString()} XOF
    </p>
    <div className="flex flex-col gap-2 pt-4">
      <Link
        href={result.programId ? `/formations/${result.programId}` : "/accueil"}
        className="inline-flex items-center justify-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-full font-medium transition"
      >
        Commencer la formation
        <ArrowRight className="w-4 h-4" />
      </Link>
      <Link
        href="/paiements"
        className="text-sm text-muted-foreground hover:text-orange-500 transition"
      >
        Voir mes paiements
      </Link>
    </div>
  </div>
)}
```

Update the **failure state** to include a retry button:

```tsx
{result && result.status !== "completed" && (
  <div className="text-center space-y-4">
    <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
      <XCircle className="w-8 h-8 text-red-600" />
    </div>
    <h1 className="text-2xl font-bold">Paiement échoué</h1>
    {result.programName && (
      <p className="text-muted-foreground">{result.programName}</p>
    )}
    <div className="flex flex-col gap-2 pt-4">
      {result.enrollmentId && (
        <Link
          href={`/paiement/${result.enrollmentId}`}
          className="inline-flex items-center justify-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-full font-medium transition"
        >
          Réessayer le paiement
        </Link>
      )}
      <Link
        href="/contact"
        className="text-sm text-muted-foreground hover:text-orange-500 transition"
      >
        Contacter le support
      </Link>
    </div>
  </div>
)}
```

Add `ArrowRight` to the lucide-react imports.

- [ ] **Step 2: Build and verify**

```bash
cd /Users/joetec/Documents/coding/brad_projects/booster_week_web
npm run build
```

- [ ] **Step 3: Commit**

```bash
git add src/app/\(public\)/paiement/confirmation/page.tsx
git commit -m "feat: enhance confirmation page with program info, retry, and next steps"
```

---

### Task 13: Payment History Screen (Flutter)

**Files:**
- Create: `booster_week/lib/features/payment/screens/payment_history_screen.dart`
- Modify: `booster_week/lib/core/services/payment_service.dart`
- Modify: `booster_week/lib/app/router.dart`
- Modify: `booster_week/lib/shared/widgets/app_drawer.dart:166-174`

- [ ] **Step 1: Add getPaymentHistory to payment service**

In `lib/core/services/payment_service.dart`, after the `verifyPayment` method, add:

```dart
Future<List<Map<String, dynamic>>> getPaymentHistory({String? status, String? method}) async {
  final params = <String, dynamic>{};
  if (status != null) params['status'] = status;
  if (method != null) params['method'] = method;
  final response = await ApiConfig.dio.get('/payments/history', queryParameters: params);
  return List<Map<String, dynamic>>.from(response.data['data']);
}
```

- [ ] **Step 2: Create payment history screen**

Create `lib/features/payment/screens/payment_history_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:booster_week/core/services/payment_service.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:intl/intl.dart';

class PaymentHistoryScreen extends ConsumerStatefulWidget {
  const PaymentHistoryScreen({super.key});

  @override
  ConsumerState<PaymentHistoryScreen> createState() => _PaymentHistoryScreenState();
}

class _PaymentHistoryScreenState extends ConsumerState<PaymentHistoryScreen> {
  List<Map<String, dynamic>> _payments = [];
  bool _loading = true;
  String _filter = '';

  static const _filters = [
    {'value': '', 'label': 'Tous'},
    {'value': 'completed', 'label': 'Complétés'},
    {'value': 'failed', 'label': 'Échoués'},
    {'value': 'expired', 'label': 'Expirés'},
    {'value': 'pending', 'label': 'En attente'},
  ];

  static const _statusLabels = {
    'completed': 'Complété',
    'pending': 'En attente',
    'failed': 'Échoué',
    'expired': 'Expiré',
  };

  static const _statusColors = {
    'completed': Colors.green,
    'pending': Colors.orange,
    'failed': Colors.red,
    'expired': Colors.grey,
  };

  static const _methodLabels = {
    'orangeMoney': 'Orange Money',
    'mtnMoney': 'MTN Money',
    'wave': 'Wave',
  };

  @override
  void initState() {
    super.initState();
    _fetchPayments();
  }

  Future<void> _fetchPayments() async {
    setState(() => _loading = true);
    try {
      final payments = await PaymentService().getPaymentHistory(
        status: _filter.isEmpty ? null : _filter,
      );
      setState(() {
        _payments = payments;
        _loading = false;
      });
    } catch (_) {
      setState(() {
        _payments = [];
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Paiements')),
      body: Column(
        children: [
          // Filter chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: _filters.map((f) {
                final isActive = _filter == f['value'];
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(f['label']!),
                    selected: isActive,
                    onSelected: (_) {
                      setState(() => _filter = f['value']!);
                      _fetchPayments();
                    },
                    selectedColor: Colors.orange.shade100,
                    checkmarkColor: Colors.orange,
                  ),
                );
              }).toList(),
            ),
          ),
          // Payment list
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _payments.isEmpty
                    ? const Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.credit_card, size: 48, color: Colors.grey),
                            SizedBox(height: 16),
                            Text('Aucun paiement pour le moment'),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _fetchPayments,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _payments.length,
                          itemBuilder: (context, index) {
                            final p = _payments[index];
                            final status = p['status'] as String? ?? 'pending';
                            final method = p['method'] as String? ?? '';
                            final amount = p['amount'] as num? ?? 0;
                            final date = DateTime.tryParse(p['date'] ?? '') ?? DateTime.now();
                            final programName = p['programName'] as String? ?? '';
                            final imageUrl = p['programImageUrl'] as String? ?? '';

                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              child: ListTile(
                                leading: imageUrl.isNotEmpty
                                    ? ClipRRect(
                                        borderRadius: BorderRadius.circular(8),
                                        child: CachedNetworkImage(
                                          imageUrl: imageUrl,
                                          width: 48,
                                          height: 48,
                                          fit: BoxFit.cover,
                                        ),
                                      )
                                    : const CircleAvatar(
                                        child: Icon(Icons.phone_android),
                                      ),
                                title: Text(programName, maxLines: 1, overflow: TextOverflow.ellipsis),
                                subtitle: Text(
                                  '${_methodLabels[method] ?? method} • ${DateFormat('d MMM yyyy', 'fr').format(date)}',
                                ),
                                trailing: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text(
                                      '${NumberFormat('#,###').format(amount)} XOF',
                                      style: const TextStyle(fontWeight: FontWeight.bold),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: (_statusColors[status] ?? Colors.grey).withOpacity(0.1),
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: Text(
                                        _statusLabels[status] ?? status,
                                        style: TextStyle(
                                          fontSize: 11,
                                          color: _statusColors[status] ?? Colors.grey,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }
}
```

- [ ] **Step 3: Add route in router.dart**

In `lib/app/router.dart`, add after the Payment route (after line 270):

```dart
GoRoute(
  path: '/payment-history',
  builder: (context, state) => const PaymentHistoryScreen(),
),
```

Add the import:
```dart
import 'package:booster_week/features/payment/screens/payment_history_screen.dart';
```

- [ ] **Step 4: Add "Paiements" to app drawer**

In `lib/shared/widgets/app_drawer.dart`, after the "My Profile" entry (after line 174), add:

```dart
ListTile(
  leading: const Icon(Icons.credit_card),
  title: const Text('Paiements'),
  onTap: () {
    Navigator.pop(context);
    context.push('/payment-history');
  },
),
```

- [ ] **Step 5: Commit**

```bash
cd /Users/joetec/Documents/coding/brad_projects/booster_week
git add lib/features/payment/screens/payment_history_screen.dart lib/core/services/payment_service.dart lib/app/router.dart lib/shared/widgets/app_drawer.dart
git commit -m "feat: add payment history screen with filters"
```

---

### Task 14: Browse Programs from Dashboard (Web + Flutter)

**Files:**
- Modify: `booster_week_web/src/app/(student)/accueil/page.tsx:17-22`
- Modify: `booster_week_web/src/components/layouts/student-layout.tsx:37-44`
- Modify: `booster_week/lib/features/home/screens/home_screen.dart`

- [ ] **Step 1: Add "Découvrir les programmes" to web dashboard quick actions**

In `src/app/(student)/accueil/page.tsx`, in the `quickActions` array (lines 17-22), add:

```tsx
{ icon: Compass, label: "Programmes", href: "/programmes" },
```

Add `Compass` to the lucide-react import.

- [ ] **Step 2: Add "Programmes" to web sidebar**

In `src/components/layouts/student-layout.tsx`, in the sidebar links array (lines 37-44), add after Formations:

```tsx
{ href: "/programmes", icon: Compass, label: "Programmes" },
```

Add `Compass` to the lucide-react import.

- [ ] **Step 3: Build web**

```bash
cd /Users/joetec/Documents/coding/brad_projects/booster_week_web
npm run build
```

- [ ] **Step 4: Commit web changes**

```bash
git add src/app/\(student\)/accueil/page.tsx src/components/layouts/student-layout.tsx
git commit -m "feat: add program discovery links to dashboard and sidebar"
```

- [ ] **Step 5: Add programs card to Flutter home screen**

In `lib/features/home/screens/home_screen.dart`, check where `QuickActionGrid` is used (line 264). This widget likely lives in a shared location. Add a "Programmes" quick action that navigates to the programs list screen. The exact implementation depends on how `QuickActionGrid` defines its items — add a new item with icon `Icons.explore` and route `/program` (the programs list route).

- [ ] **Step 6: Commit Flutter changes**

```bash
cd /Users/joetec/Documents/coding/brad_projects/booster_week
git add lib/
git commit -m "feat: add program discovery to Flutter home screen"
```

---

### Task 15: Final Deployment

- [ ] **Step 1: Deploy backend with all changes**

```bash
rsync -avz /Users/joetec/Documents/coding/brad_projects/booster_week_backend/ bib-vps:/home/ubuntu/apps/booster-week-api/ --exclude='.git' --exclude='__pycache__' --exclude='.env' --exclude='db.sqlite3'
ssh bib-vps "cd /home/ubuntu/apps/booster-week-api && docker compose up -d --build web"
```

- [ ] **Step 2: Deploy frontend with all changes**

```bash
rsync -avz /Users/joetec/Documents/coding/brad_projects/booster_week_web/ bib-vps:/home/ubuntu/apps/booster-week-web/ --exclude='.git' --exclude='node_modules' --exclude='.next' --exclude='.env'
ssh bib-vps "cd /home/ubuntu/apps/booster-week-web && docker compose up -d --build"
```

- [ ] **Step 3: Verify all endpoints**

```bash
# Payment history endpoint
curl -s https://api.boosterweekcenter.com/api/v1/payments/history -H "Authorization: Bearer TOKEN" | python3 -m json.tool

# Enriched verify response
curl -s "https://api.boosterweekcenter.com/api/v1/payments/verify?token=test" | python3 -m json.tool

# Frontend loads
curl -s -o /dev/null -w '%{http_code}' https://boosterweekcenter.com/paiements
```

- [ ] **Step 4: Visual smoke test with Chrome DevTools**

Navigate through the full flow in browser:
1. Homepage → Login → Dashboard (check "Programmes" link)
2. Programmes → Program detail (check conditional CTA)
3. Quick-enroll → Payment → MoneyFusion redirect
4. Payment history page (check filters)
