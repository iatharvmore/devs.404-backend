"""
Fires a plain-text email at the end of a run via SMTP (defaults to Gmail —
use an App Password, not your normal password, if SMTP_HOST is gmail).
"""
from __future__ import annotations

import smtplib
from email.mime.text import MIMEText


def send_email(
    subject: str,
    body: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    to_addr: str,
) -> None:
    if not (smtp_user and smtp_password and to_addr):
        print("[notify] SMTP not configured — skipping email, printing instead:")
        print(subject)
        print(body)
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_addr

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [to_addr], msg.as_string())
