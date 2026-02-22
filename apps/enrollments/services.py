import hashlib
import hmac
import logging
import time

import requests
from django.conf import settings

from apps.core.utils import generate_prefixed_id

logger = logging.getLogger(__name__)

# Map frontend method names to MoneyFusion API method codes
METHOD_MAP = {
    'orangeMoney': 'ORANGE_CI',
    'mtnMoney': 'MTN_CI',
    'wave': 'WAVE_CI',
}


class MoneyFusionService:
    """MoneyFusion payment gateway integration.

    In dev mode (MONEYFUSION_DEV_MODE=True), creates payment with a fake
    transaction ID. Use the /payments/dev-simulate endpoint to trigger
    the webhook callback locally and complete the payment.

    In production mode, calls the real MoneyFusion API.
    """

    @staticmethod
    def initiate_payment(payment, phone):
        """Initiate a payment with MoneyFusion.

        Args:
            payment: Payment model instance (must have .id, .amount, .method)
            phone: Customer phone number (e.g. '+22507XXXXXXXX')

        Returns:
            dict with keys: success, transactionId, paymentUrl (optional), expiresAt (optional)

        Raises:
            MoneyFusionError: If the API call fails
        """
        if settings.MONEYFUSION_DEV_MODE:
            transaction_id = f'txn_dev_{int(time.time() * 1000)}'
            logger.info(
                '[DEV] Payment initiated: id=%s, txn=%s, amount=%s, method=%s, phone=%s',
                payment.id, transaction_id, payment.amount, payment.method, phone,
            )
            return {
                'success': True,
                'transactionId': transaction_id,
                'paymentUrl': None,
                'expiresAt': None,
            }

        # Production: call MoneyFusion API
        mf_method = METHOD_MAP.get(payment.method, payment.method)
        payload = {
            'amount': payment.amount,
            'currency': 'XOF',
            'method': mf_method,
            'phone': phone,
            'orderId': str(payment.id),
            'callbackUrl': settings.MONEYFUSION_WEBHOOK_URL,
            'description': f'Paiement Booster Week - {payment.id}',
        }

        try:
            response = requests.post(
                f'{settings.MONEYFUSION_BASE_URL}/transactions',
                json=payload,
                headers={
                    'Authorization': f'Bearer {settings.MONEYFUSION_API_KEY}',
                    'Content-Type': 'application/json',
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            logger.info(
                'MoneyFusion payment initiated: id=%s, txn=%s',
                payment.id, data.get('transactionId'),
            )

            return {
                'success': True,
                'transactionId': data['transactionId'],
                'paymentUrl': data.get('paymentUrl'),
                'expiresAt': data.get('expiresAt'),
            }

        except requests.exceptions.Timeout:
            logger.error('MoneyFusion timeout for payment %s', payment.id)
            raise MoneyFusionError('Payment gateway timeout. Please try again.')

        except requests.exceptions.ConnectionError:
            logger.error('MoneyFusion connection error for payment %s', payment.id)
            raise MoneyFusionError('Unable to reach payment gateway. Please try again later.')

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            body = ''
            try:
                body = e.response.json() if e.response else {}
            except Exception:
                body = e.response.text if e.response else ''

            logger.error(
                'MoneyFusion HTTP %s for payment %s: %s',
                status_code, payment.id, body,
            )

            if status_code == 401:
                raise MoneyFusionError('Payment gateway authentication failed.')
            elif status_code == 422:
                msg = body.get('message', 'Invalid payment data') if isinstance(body, dict) else 'Invalid payment data'
                raise MoneyFusionError(f'Payment rejected: {msg}')
            else:
                raise MoneyFusionError(f'Payment gateway error (HTTP {status_code}).')

        except Exception as e:
            logger.exception('Unexpected MoneyFusion error for payment %s', payment.id)
            raise MoneyFusionError(f'Unexpected payment error: {str(e)}')

    @staticmethod
    def verify_webhook_signature(payload, provided_signature):
        """Verify MoneyFusion webhook HMAC-SHA256 signature.

        The signing string is built from alphabetically-ordered fields
        joined by '|', then HMAC-SHA256 signed with the webhook secret.
        """
        if not provided_signature:
            return False

        fields = ['amount', 'currency', 'method', 'orderId', 'phone',
                  'status', 'timestamp', 'transactionId']
        values = [str(payload.get(f, '')) for f in fields]
        signing_string = '|'.join(values)

        expected = hmac.new(
            settings.MONEYFUSION_WEBHOOK_SECRET.encode(),
            signing_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, provided_signature)

    @staticmethod
    def build_dev_webhook_payload(payment):
        """Build a valid webhook payload for dev simulation.

        Returns a payload dict with valid signature for local testing.
        """
        payload = {
            'transactionId': payment.mf_transaction_id or '',
            'orderId': str(payment.id),
            'status': 'completed',
            'amount': str(payment.amount),
            'currency': 'XOF',
            'method': METHOD_MAP.get(payment.method, payment.method),
            'phone': '',
            'timestamp': str(int(time.time())),
        }

        # Build valid signature
        fields = ['amount', 'currency', 'method', 'orderId', 'phone',
                  'status', 'timestamp', 'transactionId']
        values = [str(payload.get(f, '')) for f in fields]
        signing_string = '|'.join(values)

        signature = hmac.new(
            settings.MONEYFUSION_WEBHOOK_SECRET.encode(),
            signing_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        payload['signature'] = signature
        return payload


class MoneyFusionError(Exception):
    """Raised when MoneyFusion API call fails."""
    pass
