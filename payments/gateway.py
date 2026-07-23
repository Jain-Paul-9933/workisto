"""
The payment gateway boundary.

Everything the rest of the app knows about "a payment processor" is these two
methods: create an intent, and verify an incoming webhook. Stripe lives behind
`StripeGateway`; tests (and a keyless dev box) use `FakeGateway`. Which one is
live is a settings switch, so no test ever touches the network or needs Stripe
keys, and swapping processors later touches exactly one file.

`stripe` is imported lazily inside StripeGateway so the package isn't even
required unless you actually run against Stripe.
"""

import json
from dataclasses import dataclass

from django.conf import settings


@dataclass
class Intent:
    id: str
    client_secret: str


@dataclass
class WebhookEvent:
    type: str
    intent_id: str


class WebhookError(Exception):
    """Raised when an incoming webhook fails signature verification."""


class StripeGateway:
    def __init__(self, secret_key, webhook_secret):
        self.secret_key = secret_key
        self.webhook_secret = webhook_secret

    def create_intent(self, *, amount, currency, metadata):
        import stripe

        stripe.api_key = self.secret_key
        intent = stripe.PaymentIntent.create(
            amount=amount,  # minor units (paise/cents)
            currency=currency,
            metadata=metadata,
            automatic_payment_methods={"enabled": True},
        )
        return Intent(id=intent.id, client_secret=intent.client_secret)

    def verify_webhook(self, payload, sig_header):
        import stripe

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret,
            )
        except Exception as exc:  # ValueError or SignatureVerificationError
            raise WebhookError(str(exc)) from exc
        return WebhookEvent(
            type=event["type"], intent_id=event["data"]["object"]["id"],
        )


class FakeGateway:
    """Deterministic stand-in for tests and keyless local dev."""

    VALID_SIGNATURE = "sig_ok"

    def create_intent(self, *, amount, currency, metadata):
        pid = metadata.get("payment_id", "x")
        return Intent(id=f"pi_fake_{pid}", client_secret=f"pi_fake_{pid}_secret")

    def verify_webhook(self, payload, sig_header):
        if sig_header != self.VALID_SIGNATURE:
            raise WebhookError("bad signature")
        if isinstance(payload, bytes):
            payload = payload.decode()
        data = json.loads(payload)
        return WebhookEvent(
            type=data["type"], intent_id=data["data"]["object"]["id"],
        )


def get_gateway():
    """The configured gateway. Not cached, so tests can flip PAYMENT_GATEWAY."""
    if settings.PAYMENT_GATEWAY == "stripe":
        return StripeGateway(settings.STRIPE_SECRET_KEY, settings.STRIPE_WEBHOOK_SECRET)
    return FakeGateway()
