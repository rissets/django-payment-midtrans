import base64
import hashlib
import logging

import requests

from django_midtrans.app_settings import midtrans_settings
from django_midtrans.exceptions import (
    MidtransAPIError,
    MidtransAuthenticationError,
    MidtransDuplicateOrderError,
    MidtransRateLimitError,
    MidtransValidationError,
)

logger = logging.getLogger("django_midtrans")


class MidtransClient:
    """
    Low-level HTTP client for Midtrans Core API.
    Thread-safe, stateless — reuse a single instance.
    """

    def __init__(self, server_key=None, is_production=None):
        self.server_key = server_key or midtrans_settings.SERVER_KEY
        if is_production is None:
            is_production = midtrans_settings.IS_PRODUCTION
        self.base_url = "https://api.midtrans.com" if is_production else "https://api.sandbox.midtrans.com"
        self._session = requests.Session()
        self._session.headers.update(self._get_headers())

    def _get_headers(self):
        auth_string = base64.b64encode(f"{self.server_key}:".encode()).decode()
        return {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _handle_response(self, response):
        status = response.status_code
        try:
            data = response.json()
        except ValueError:
            data = {"status_code": str(status), "status_message": response.text}

        if status == 401:
            raise MidtransAuthenticationError(data.get("status_message", "Authentication failed"))
        elif status == 406:
            raise MidtransDuplicateOrderError(data.get("status_message", "Duplicate order ID"))
        elif status == 429:
            raise MidtransRateLimitError("Rate limit exceeded")
        elif status == 400:
            raise MidtransValidationError(data.get("status_message", "Validation error"), data=data)
        elif status >= 400:
            raise MidtransAPIError(
                data.get("status_message", f"API error {status}"),
                status_code=status,
                data=data,
            )

        return data

    def _request(self, method, path, json=None, timeout=30):
        url = f"{self.base_url}{path}"
        logger.debug("Midtrans %s %s", method.upper(), url)
        try:
            response = self._session.request(method, url, json=json, timeout=timeout)
        except requests.RequestException as e:
            logger.error("Midtrans request failed: %s", str(e))
            raise MidtransAPIError(f"Request failed: {e}") from e
        return self._handle_response(response)

    # ─── Core Payment API ───────────────────────────────────

    def charge(self, payload):
        return self._request("POST", "/v2/charge", json=payload)

    def get_status(self, order_id):
        return self._request("GET", f"/v2/{order_id}/status")

    def get_status_b2b(self, order_id):
        return self._request("GET", f"/v2/{order_id}/status/b2b")

    def cancel(self, order_id):
        return self._request("POST", f"/v2/{order_id}/cancel")

    def expire(self, order_id):
        return self._request("POST", f"/v2/{order_id}/expire")

    def capture(self, transaction_id, gross_amount):
        return self._request("POST", "/v2/capture", json={
            "transaction_id": transaction_id,
            "gross_amount": gross_amount,
        })

    def refund(self, order_id, refund_key, amount, reason=""):
        payload = {
            "refund_key": refund_key,
            "amount": amount,
            "reason": reason,
        }
        return self._request("POST", f"/v2/{order_id}/refund", json=payload)

    def direct_refund(self, order_id, refund_key, amount, reason=""):
        payload = {
            "refund_key": refund_key,
            "amount": amount,
            "reason": reason,
        }
        return self._request("POST", f"/v2/{order_id}/refund/online/direct", json=payload)

    def approve(self, order_id):
        return self._request("POST", f"/v2/{order_id}/approve")

    def deny(self, order_id):
        return self._request("POST", f"/v2/{order_id}/deny")

    # ─── Card Specific ──────────────────────────────────────

    def get_card_token(self, card_number, card_exp_month, card_exp_year, card_cvv, client_key=None):
        client_key = client_key or midtrans_settings.CLIENT_KEY
        return self._request("GET", f"/v2/token?card_number={card_number}"
                             f"&card_exp_month={card_exp_month}"
                             f"&card_exp_year={card_exp_year}"
                             f"&card_cvv={card_cvv}"
                             f"&client_key={client_key}")

    def register_card(self, card_number, card_exp_month, card_exp_year, client_key=None):
        client_key = client_key or midtrans_settings.CLIENT_KEY
        return self._request("GET", f"/v2/card/register?card_number={card_number}"
                             f"&card_exp_month={card_exp_month}"
                             f"&card_exp_year={card_exp_year}"
                             f"&client_key={client_key}")

    def point_inquiry(self, token_id):
        return self._request("GET", f"/v2/point_inquiry/{token_id}")

    def get_bin(self, bin_number):
        return self._request("GET", f"/v1/bins/{bin_number}")

    # ─── Pay Account (GoPay Tokenization) ───────────────────

    def create_pay_account(self, payload):
        return self._request("POST", "/v2/pay/account", json=payload)

    def get_pay_account(self, account_id):
        return self._request("GET", f"/v2/pay/account/{account_id}")

    def unbind_pay_account(self, account_id):
        return self._request("POST", f"/v2/pay/account/{account_id}/unbind")

    # ─── Subscription API ───────────────────────────────────

    def create_subscription(self, payload):
        return self._request("POST", "/v1/subscriptions", json=payload)

    def get_subscription(self, subscription_id):
        return self._request("GET", f"/v1/subscriptions/{subscription_id}")

    def disable_subscription(self, subscription_id):
        return self._request("POST", f"/v1/subscriptions/{subscription_id}/disable")

    def enable_subscription(self, subscription_id):
        return self._request("POST", f"/v1/subscriptions/{subscription_id}/enable")

    def cancel_subscription(self, subscription_id):
        return self._request("POST", f"/v1/subscriptions/{subscription_id}/cancel")

    def update_subscription(self, subscription_id, payload):
        return self._request("PATCH", f"/v1/subscriptions/{subscription_id}", json=payload)

    # ─── Invoice API ────────────────────────────────────────

    def create_invoice(self, payload):
        return self._request("POST", "/v1/invoices", json=payload)

    def get_invoice(self, invoice_id):
        return self._request("GET", f"/v1/invoices/{invoice_id}")

    def void_invoice(self, invoice_id, void_reason=""):
        payload = {"status": "void"}
        if void_reason:
            payload["void_reason"] = void_reason
        return self._request("PATCH", f"/v1/invoices/{invoice_id}", json=payload)

    # ─── Signature Verification ─────────────────────────────

    @staticmethod
    def verify_signature(order_id, status_code, gross_amount, signature_key, server_key=None):
        server_key = server_key or midtrans_settings.SERVER_KEY
        raw = f"{order_id}{status_code}{gross_amount}{server_key}"
        expected = hashlib.sha512(raw.encode()).hexdigest()
        return expected == signature_key


# Module-level singleton for convenience
_default_client = None


def get_client():
    global _default_client
    if _default_client is None:
        _default_client = MidtransClient()
    return _default_client
