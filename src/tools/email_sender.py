import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _require(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(
            f"{key} is not set. "
            "Make sure your .env file exists and load_dotenv() has been called."
        )
    return value


def send_html_email(subject: str, html_body: str) -> None:
    smtp_host = _require("SMTP_HOST")
    smtp_port = int(_require("SMTP_PORT"))
    email_from = _require("EMAIL_FROM")
    email_to = _require("EMAIL_TO")
    password = _require("EMAIL_PASSWORD")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = email_to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(email_from, password)
        server.sendmail(email_from, [email_to], msg.as_string())

    print(f"  Email sent to {email_to}")
