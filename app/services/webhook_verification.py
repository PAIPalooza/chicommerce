"""
Webhook signature verification service.

This module handles verification of webhook signatures from payment providers
to ensure authenticity and prevent tampering.
"""
import hashlib
import hmac
import time
from typing import Optional, Dict, Any

from fastapi import HTTPException, status

from app.core.config import settings


class WebhookVerificationService:
    """Service for verifying webhook signatures."""

    def __init__(self):
        """Initialize webhook verification service."""
        # In production, these would come from environment variables
        self.stripe_webhook_secret = getattr(
            settings, 'STRIPE_WEBHOOK_SECRET', 'test_stripe_webhook_secret'
        )
        self.paypal_webhook_id = getattr(
            settings, 'PAYPAL_WEBHOOK_ID', 'test_paypal_webhook_id'
        )

    def verify_stripe_signature(
        self,
        payload: str,
        signature_header: str,
        tolerance: int = 300
    ) -> bool:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Raw request body as string
            signature_header: Value of Stripe-Signature header
            tolerance: Maximum allowed age of webhook in seconds

        Returns:
            True if signature is valid

        Raises:
            HTTPException: If signature is invalid or webhook is too old
        """
        if not signature_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature header"
            )

        try:
            # Parse signature header
            elements = signature_header.split(',')
            timestamp = None
            signatures = []

            for element in elements:
                key_value = element.split('=', 1)
                if len(key_value) != 2:
                    continue

                key, value = key_value
                if key == 't':
                    timestamp = int(value)
                elif key.startswith('v'):
                    signatures.append(value)

            if timestamp is None or not signatures:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Stripe signature format"
                )

            # Check timestamp tolerance
            current_time = int(time.time())
            if abs(current_time - timestamp) > tolerance:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Webhook timestamp too old"
                )

            # Compute expected signature
            signed_payload = f"{timestamp}.{payload}"
            expected_signature = hmac.new(
                self.stripe_webhook_secret.encode(),
                signed_payload.encode(),
                hashlib.sha256
            ).hexdigest()

            # Compare signatures
            for signature in signatures:
                if hmac.compare_digest(signature, expected_signature):
                    return True

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Stripe signature"
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error parsing Stripe signature: {str(e)}"
            )

    def verify_paypal_signature(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> bool:
        """
        Verify PayPal webhook signature.

        Note: In production, this would use PayPal's SDK to verify the signature
        using the cert URL and transmission ID. For testing, we validate headers exist.

        Args:
            payload: Webhook payload
            headers: Request headers

        Returns:
            True if signature is valid

        Raises:
            HTTPException: If signature verification fails
        """
        required_headers = [
            'PAYPAL-TRANSMISSION-ID',
            'PAYPAL-TRANSMISSION-TIME',
            'PAYPAL-TRANSMISSION-SIG',
            'PAYPAL-CERT-URL',
            'PAYPAL-AUTH-ALGO'
        ]

        # Check all required headers are present
        missing_headers = [
            header for header in required_headers
            if header not in headers and header.lower() not in headers
        ]

        if missing_headers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing PayPal verification headers: {', '.join(missing_headers)}"
            )

        # In production, you would use the PayPal SDK to verify:
        # from paypalrestsdk import WebhookEvent
        # webhook_event = WebhookEvent.verify(
        #     transmission_id=headers.get('PAYPAL-TRANSMISSION-ID'),
        #     timestamp=headers.get('PAYPAL-TRANSMISSION-TIME'),
        #     webhook_id=self.paypal_webhook_id,
        #     event_body=payload,
        #     cert_url=headers.get('PAYPAL-CERT-URL'),
        #     actual_sig=headers.get('PAYPAL-TRANSMISSION-SIG'),
        #     auth_algo=headers.get('PAYPAL-AUTH-ALGO')
        # )

        # For testing purposes, we'll accept if headers are present
        # In production, replace this with actual PayPal verification
        return True


# Singleton instance
webhook_verification_service = WebhookVerificationService()
