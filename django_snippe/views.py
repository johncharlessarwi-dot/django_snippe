import json
import logging

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from . import signals
from .conf import get_setting
from .exceptions import WebhookPayloadError, WebhookVerificationError
from .logging import PaymentLogger
from .models import SnippePayment, SnippePayout

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class SnippeWebhookView(View):
    """
    Handles incoming webhook POST requests from Snippe.

    Usage in urls.py:
        path("payments/", include("django_snippe.urls"))

    This registers: POST /payments/webhook/
    """

    def post(self, request, *args, **kwargs):
        # Parse raw body
        try:
            body = request.body.decode("utf-8")
            data = json.loads(body)
        except (ValueError, UnicodeDecodeError) as e:
            logger.warning("Snippe webhook: invalid JSON body — %s", e)
            raise WebhookPayloadError(f"Invalid JSON body: {e}") from e

        if not isinstance(data, dict):
            raise WebhookPayloadError("Webhook payload must be an object")

        # Verify signature if webhook secret is configured
        signing_key = get_setting("WEBHOOK_SECRET")
        if signing_key:
            signature = request.headers.get("X-Webhook-Signature", "")
            timestamp = request.headers.get("X-Webhook-Timestamp", "")
            try:
                from snippe import verify_webhook
                verify_webhook(
                    body=body,
                    signature=signature,
                    timestamp=timestamp,
                    signing_key=signing_key,
                )
            except Exception as e:
                logger.warning("Snippe webhook: verification failed — %s", e)
                raise WebhookVerificationError(f"Webhook verification failed: {e}") from e

        if "data" in data and not isinstance(data["data"], dict):
            raise WebhookPayloadError("Webhook data must be an object")

        event = data.get("event")
        reference = data.get("reference") or data.get("data", {}).get("reference")

        if not isinstance(event, str) or not isinstance(reference, str) or len(event) > 80 or len(reference) > 160:
            raise WebhookPayloadError("Invalid webhook event or reference")
        if not event or not reference:
            logger.error("Snippe webhook: missing event or reference in payload")
            raise WebhookPayloadError("Missing 'event' or 'reference' in webhook payload")

        if not __import__("re").fullmatch(r"[a-z]+(?:\.[a-z_]+)*", event):
            raise WebhookPayloadError("Invalid webhook event name")

        PaymentLogger.log_webhook_received(event, reference)

        # Route to handler
        try:
            handler = getattr(self, f"handle_{event.replace('.', '_')}", None)
            if handler:
                handler(reference, data)
            else:
                logger.debug("Snippe webhook: no handler for event %s", event)
        except Exception as e:
            logger.error("Snippe webhook handler error for %s: %s", event, e, exc_info=True)
            raise

        return HttpResponse(status=200)

    def handle_payment_completed(self, reference, data):
        try:
            payment = SnippePayment.objects.get(reference=reference)
            payment.status = SnippePayment.Status.COMPLETED
            payment.save(update_fields=["status", "updated_at"])
            signals.payment_completed.send(sender=SnippePayment, payment=payment)

            logger.info("Payment %s marked as completed", reference)

        except SnippePayment.DoesNotExist:
            logger.error("Payment %s not found when handling completion", reference)

    def handle_payment_failed(self, reference, data):
        try:
            payment = SnippePayment.objects.get(reference=reference)
            payment.status = SnippePayment.Status.FAILED
            payment.save(update_fields=["status", "updated_at"])
            signals.payment_failed.send(sender=SnippePayment, payment=payment)
        except SnippePayment.DoesNotExist:
            logger.error("Payment %s not found when handling expiration", reference)

    def handle_payment_voided(self, reference, data):
        try:
            payment = SnippePayment.objects.get(reference=reference)
            payment.status = SnippePayment.Status.VOIDED
            payment.save(update_fields=["status", "updated_at"])
            signals.payment_voided.send(sender=SnippePayment, payment=payment)
            logger.info("Payment %s marked as voided", reference)
        except SnippePayment.DoesNotExist:
            logger.error("Payment %s not found when handling void", reference)

    def handle_payout_completed(self, reference, data):
        try:
            payout = SnippePayout.objects.get(reference=reference)
            payout.status = SnippePayout.Status.COMPLETED
            payout.save(update_fields=["status", "updated_at"])
            signals.payout_completed.send(sender=SnippePayout, payout=payout)
            logger.info("Payout %s marked as completed", reference)
        except SnippePayout.DoesNotExist:
            logger.error("Payout %s not found when handling completion", reference)

    def handle_payout_failed(self, reference, data):
        try:
            payout = SnippePayout.objects.get(reference=reference)
            payout.status = SnippePayout.Status.FAILED
            payout.save(update_fields=["status", "updated_at"])
            signals.payout_failed.send(sender=SnippePayout, payout=payout)
            logger.info("Payout %s marked as failed", reference)
        except SnippePayout.DoesNotExist:
            logger.error("Payout %s not found when handling failure", reference)
