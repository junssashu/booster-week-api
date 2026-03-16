import logging
import time

from django.conf import settings

logger = logging.getLogger(__name__)

# Map frontend method names to MoneyFusion API method codes
METHOD_MAP = {
    'orangeMoney': 'ORANGE_CI',
    'mtnMoney': 'MTN_CI',
    'wave': 'WAVE_CI',
}


class MoneyFusionService:
    """MoneyFusion payment gateway integration using the official apiMoneyFusion library.

    In dev mode (MONEYFUSION_DEV_MODE=True), creates payment with a fake
    transaction ID. Use the /payments/dev-simulate endpoint to trigger
    the webhook callback locally and complete the payment.

    In production mode, calls the real MoneyFusion API via PaymentClient.
    """

    @staticmethod
    def _get_client():
        """Get a configured PaymentClient instance."""
        from apiMoneyFusion import PaymentClient
        return PaymentClient(api_key_url=settings.MONEYFUSION_BASE_URL)

    @staticmethod
    def initiate_payment(payment, phone):
        """Initiate a payment with MoneyFusion.

        Args:
            payment: Payment model instance (must have .id, .amount, .method, .enrollment)
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

        # Production: call MoneyFusion API via official library
        try:
            client = MoneyFusionService._get_client()

            return_url = settings.MONEYFUSION_RETURN_URL

            articles = [{
                'name': f'Paiement Booster Week - {payment.id}',
                'price': str(payment.amount),
                'quantity': 1,
            }]

            # Get client name from enrollment user
            user = payment.enrollment.user
            client_name = f'{user.first_name} {user.last_name}'.strip() or user.phone

            result = client.create_payment(
                total_price=str(payment.amount),
                articles=articles,
                numero_send=phone,
                nom_client=client_name,
                user_id=1,
                order_id=payment.id,
                return_url=return_url,
                webhook_url=settings.MONEYFUSION_WEBHOOK_URL,
            )

            if not result.get('statut'):
                raise MoneyFusionError(
                    result.get('message', 'Payment creation failed.')
                )

            token = result['token']
            payment_url = result.get('url', '')

            logger.info(
                'MoneyFusion payment initiated: id=%s, token=%s, url=%s',
                payment.id, token, payment_url,
            )

            return {
                'success': True,
                'transactionId': token,
                'paymentUrl': payment_url,
                'expiresAt': None,
            }

        except MoneyFusionError:
            raise

        except Exception as e:
            logger.exception('Unexpected MoneyFusion error for payment %s', payment.id)
            raise MoneyFusionError(f'Unexpected payment error: {str(e)}')

    @staticmethod
    def verify_payment(token):
        """Verify payment status via MoneyFusion API.

        Args:
            token: The payment token returned from create_payment.

        Returns:
            dict with payment data including 'statut' field.
            In production, response looks like:
            {
                "statut": true,
                "data": {
                    "statut": "paid",  # "paid", "failed", "no paid", "pending"
                    "tokenPay": "...",
                    "Montant": "...",
                    ...
                }
            }
        """
        if settings.MONEYFUSION_DEV_MODE:
            return {'statut': True, 'data': {'statut': 'paid'}}

        try:
            client = MoneyFusionService._get_client()
            result = client.get_payment(token)
            return result
        except Exception as e:
            logger.exception('MoneyFusion verify error for token %s', token)
            raise MoneyFusionError(f'Payment verification failed: {str(e)}')

    @staticmethod
    def build_dev_webhook_payload(payment, simulate_status='paid'):
        """Build a MoneyFusion-format webhook payload for dev simulation.

        Args:
            payment: Payment model instance
            simulate_status: 'paid' or 'failed' (MoneyFusion status values)

        Returns:
            dict matching MoneyFusion's real webhook format
        """
        return {
            'statut': True,
            'data': {
                'tokenPay': payment.mf_transaction_id or '',
                'numeroSend': '',
                'nomclient': 'Dev User',
                'personal_Info': [],
                'numeroTransaction': f'dev_txn_{int(time.time())}',
                'Montant': str(payment.amount),
                'frais': '0',
                'statut': simulate_status,
                'moyen': METHOD_MAP.get(payment.method, payment.method),
                'return_url': settings.MONEYFUSION_RETURN_URL,
                'createdAt': '',
            },
        }


class MoneyFusionError(Exception):
    """Raised when MoneyFusion API call fails."""
    pass
