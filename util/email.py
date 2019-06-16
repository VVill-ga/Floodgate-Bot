from email.message import EmailMessage
import smtplib
import textwrap

from secret import EMAIL_USERNAME, EMAIL_PASSWORD

def validate_email(address):
    valid_domains = [
        "oregonstate.edu",
        "onid.orst.edu"
    ]

    return address.split("@")[1] in valid_domains

def send_confirmation(address, token):
    body = """\
        Welcome to the OSU Security Club! In order to verify your membership, please send the following token in a private message to the OSUSEC bot that messaged you:

        {token}

        Message an Officer if you have any questions. Thanks, and welcome!\
        """.format(token=token)

    msg = EmailMessage()
    msg['From'] = "noreply@osusec.org"
    msg['To'] = address
    msg['Subject'] = "OSUSEC Discord Email Confirmation"

    msg.set_content(textwrap.dedent(body))

    with smtplib.SMTP_SSL("secure234.inmotionhosting.com", 465) as server:
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.send_message(msg)