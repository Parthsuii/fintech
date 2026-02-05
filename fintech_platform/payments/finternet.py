import os
import time
import requests


FINTERNET_API_KEY = os.getenv("FINTERNET_API_KEY")

BASE_URL = "https://api.fmm.finternetlab.io/v1"


def create_finternet_dvp_payment(amount, reference_id, metadata):

    print("FINTERNET KEY:", FINTERNET_API_KEY)

    if not FINTERNET_API_KEY:
        print("❌ No API key")

        return demo_fallback(reference_id, amount)

    try:
        response = requests.post(
            f"{BASE_URL}/payment-intents",
            headers={
                "X-API-Key": FINTERNET_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "amount": amount,
                "currency": "USDC",
                "type": "DELIVERY_VS_PAYMENT",
                "settlementMethod": "OFF_RAMP_MOCK",
                "settlementDestination": "bank_account_123",
                "description": f"Investment {reference_id}",
                "metadata": metadata,
            },
            timeout=15,
        )

        print("FINTERNET STATUS:", response.status_code)
        print("FINTERNET RESPONSE:", response.text)

        if response.status_code != 200:
            return demo_fallback(reference_id, amount)

        return response.json()

    except Exception as e:
        print("❌ FINTERNET ERROR:", e)

        return demo_fallback(reference_id, amount)


# -------------------------
# DEMO FALLBACK
# -------------------------

def demo_fallback(reference_id, amount):

    print("⚠️ USING DEMO MODE")

    fake_intent = f"demo_{int(time.time())}"

    return {
        "data": {
            "id": fake_intent,
            "paymentUrl": f"http://127.0.0.1:8000/api/callback/{fake_intent}/",
            "amount": amount,
            "status": "INITIATED",
            "reference": reference_id,
        }
    }
