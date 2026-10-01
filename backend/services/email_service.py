import os
import smtplib
import ssl

from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# EMAIL CONFIGURATION
# ============================================================

MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

MAIL_DEFAULT_SENDER = os.getenv(
    "MAIL_DEFAULT_SENDER",
    MAIL_USERNAME,
)


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(
    recipient,
    subject,
    body,
):

    if not MAIL_USERNAME or not MAIL_PASSWORD:
        raise RuntimeError(
            "Email credentials are missing from .env"
        )

    message = EmailMessage()

    message["From"] = MAIL_DEFAULT_SENDER
    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(body)


    context = ssl.create_default_context()


    with smtplib.SMTP(
        MAIL_SERVER,
        MAIL_PORT,
        timeout=30,
    ) as server:

        server.ehlo()

        server.starttls(
            context=context
        )

        server.ehlo()

        server.login(
            MAIL_USERNAME,
            MAIL_PASSWORD,
        )

        server.send_message(
            message
        )