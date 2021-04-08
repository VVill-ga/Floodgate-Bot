from email.message import EmailMessage
import smtplib
import textwrap

from config import EMAIL_SERVER, EMAIL_USERNAME, EMAIL_PASSWORD, VALID_EMAIL_DOMAINS


def is_valid_email(address):
    try:
        return (
            len(address.split("@")) == 2
            and address.split("@")[1] in VALID_EMAIL_DOMAINS
            and "," not in address
        )
    except:
        return False


def send_confirmation(address, token):
    body = f"""
Welcome to the OSU Security Club! In order to verify your membership, please send the following token in a private message to the OSUSEC bot that messaged you:

{token}

Message an Officer if you have any questions. Thanks, and welcome!
    """  # noqa: E501

    msg = EmailMessage()
    msg["From"] = EMAIL_USERNAME
    msg["To"] = address
    msg["Subject"] = "OSUSEC Discord Email Confirmation"

    msg.set_content(textwrap.dedent(body))

    with smtplib.SMTP_SSL(EMAIL_SERVER, 465) as server:
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.send_message(msg)
