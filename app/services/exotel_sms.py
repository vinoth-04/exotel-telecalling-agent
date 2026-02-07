import os
import requests
from requests.auth import HTTPBasicAuth


def send_exotel_sms(to_phone: str, message: str) -> bool:
    """
    Sends SMS using Exotel API.
    Returns True if success, False otherwise.
    """

    ACCOUNT_SID = os.getenv("EXOTEL_ACCOUNT_SID")
    API_KEY = os.getenv("EXOTEL_API_KEY")
    API_TOKEN = os.getenv("EXOTEL_API_TOKEN")
    SENDER_ID = os.getenv("EXOTEL_SENDER_ID")

    url = f"https://api.exotel.com/v1/Accounts/{ACCOUNT_SID}/Sms/send.json"

    payload = {
        "From": SENDER_ID,
        "To": to_phone,
        "Body": message
    }

    response = requests.post(
        url,
        data=payload,
        auth=HTTPBasicAuth(API_KEY, API_TOKEN),
        timeout=10
    )

    if response.status_code == 200:
        print(f"📨 SMS SENT to {to_phone}")
        return True
    else:
        print("❌ Exotel SMS FAILED:", response.text)
        return False
