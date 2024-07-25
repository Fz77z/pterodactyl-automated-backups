import logging
import os
import smtplib
from email.message import EmailMessage

__all__ = ["EmailAlert"]


logger = logging.getLogger(__name__)


class EmailAlert:
    def __init__(self):
        self.from_email: str = os.getenv("FROM_EMAIL")
        self.from_password: str = os.getenv("FROM_PASSWORD")
        self.smtp_server: str = os.getenv("SMTP_SERVER")
        self.smtp_port: int = int(os.getenv("SMTP_PORT"))

    @staticmethod
    def _anonymize_email(email):
        local_part, domain = email.split("@")
        return f"{'*' * len(local_part)}@{domain}"

    def send(self, subject: str, body: str, to_email: str):
        if not all(
            isinstance(i, str)
            for i in [subject, body, to_email, self.from_email, self.from_password]
        ):
            raise ValueError("All parameters must be of type str")

        logger.info(f"Preparing to send email to {self._anonymize_email(to_email)}")

        # Create the email message
        msg = EmailMessage()
        msg.set_content(body.rstrip())
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = to_email

        try:
            # Connect to the mail server using TLS
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                # Enable TLS encryption
                server.starttls()
                # Log in to your email account
                server.login(self.from_email, self.from_password)

                # Send the email
                server.send_message(msg)
                logger.info(f"Email sent to {self._anonymize_email(to_email)}")
        except smtplib.SMTPException as e:
            logger.error(
                f"SMTP error occurred when sending email to {self._anonymize_email(to_email)}: {e}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error occurred when sending email to {self._anonymize_email(to_email)}: {e}"
            )
