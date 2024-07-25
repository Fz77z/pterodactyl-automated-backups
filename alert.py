import smtplib
from common import logger
from email.message import EmailMessage


class EmailAlert:
    def __init__(self, from_email, from_password, smtp_server, smtp_port):
        self.from_email = from_email
        self.from_password = from_password
        self.smtp_server = smtp_server
        self.smtp_port = int(smtp_port)

    def anonymize_email(self, email):
        local_part, domain = email.split("@")
        return f"{'*' * len(local_part)}@{domain}"

    def send(self, subject, body, to_email):
        if not all(
            isinstance(i, str)
            for i in [subject, body, to_email, self.from_email, self.from_password]
        ):
            raise ValueError("All parameters must be of type str")

        logger.info(f"Preparing to send email to {self.anonymize_email(to_email)}")

        # Create the email message
        msg = EmailMessage()
        msg.set_content(body)
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
                logger.info(f"Email sent to {self.anonymize_email(to_email)}")
        except smtplib.SMTPException as e:
            logger.error(
                f"SMTP error occurred when sending email to {self.anonymize_email(to_email)}: {e}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error occurred when sending email to {self.anonymize_email(to_email)}: {e}"
            )
