"""
Safe Email Sender with daily limit
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from typing import Optional
from config.settings import (
    SMTP_EMAIL,
    SMTP_APP_PASSWORD,
    SMTP_HOST,
    SMTP_PORT,
    DAILY_EMAIL_LIMIT,
    STUDENT_NAME,
    STUDENT_EMAIL,
)
from database.db import get_session, EmailLog, Contact


class EmailSender:
    def __init__(self):
        if not SMTP_EMAIL or not SMTP_APP_PASSWORD:
            raise ValueError("SMTP credentials missing in .env")
        self.from_email = SMTP_EMAIL
        self.password = SMTP_APP_PASSWORD
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.limit = DAILY_EMAIL_LIMIT

    def count_sent_today(self) -> int:
        session = get_session()
        today = date.today()
        count = (
            session.query(EmailLog)
            .filter(EmailLog.status == "sent")
            .filter(EmailLog.sent_at >= datetime.combine(today, datetime.min.time()))
            .count()
        )
        session.close()
        return count

    def send(
        self,
        to_email: str,
        subject: str,
        body: str,
        contact_id: int = None,
        email_type: str = "initial",
        dry_run: bool = False,
    ) -> bool:
        if self.count_sent_today() >= self.limit:
            print(f"[LIMIT] Daily limit {self.limit} reached")
            return False

        if dry_run:
            print(f"[DRY-RUN] To: {to_email} | {subject}")
            return True

        msg = MIMEMultipart()
        msg["From"] = f"{STUDENT_NAME} <{self.from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Reply-To"] = STUDENT_EMAIL or self.from_email
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.from_email, self.password)
                server.send_message(msg)

            # Update log
            session = get_session()
            if contact_id:
                log = (
                    session.query(EmailLog)
                    .filter(EmailLog.contact_id == contact_id)
                    .filter(EmailLog.email_type == email_type)
                    .filter(EmailLog.status.in_(["draft", "approved"]))
                    .order_by(EmailLog.id.desc())
                    .first()
                )
                if log:
                    log.status = "sent"
                    log.sent_at = datetime.utcnow()
                # Update contact status
                contact = session.query(Contact).filter(Contact.id == contact_id).first()
                if contact:
                    contact.status = "sent"
                session.commit()
            session.close()
            print(f"[SENT] → {to_email}")
            return True
        except Exception as e:
            print(f"[ERROR] {e}")
            return False