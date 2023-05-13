import os
import smtplib
import logging
from email.message import EmailMessage
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# Set up logging
logging.basicConfig(filename='backup.log', filemode='a', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def anonymize_email(email):
    """Replace the local part of the email with asterisks.

    Args:
        email (str): The email address to anonymize.

    Returns:
        str: The anonymized email address.
    """
    local_part, domain = email.split('@')
    return f"{'*' * len(local_part)}@{domain}"

def send_email(subject, body, to_email, from_email, from_password):
    """Send an email.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email.
        to_email (str): The recipient's email address.
        from_email (str): The sender's email address.
        from_password (str): The password for the sender's email account.

    Raises:
        ValueError: If any of the parameters are not of type str.
    """
    if not all(isinstance(i, str) for i in [subject, body, to_email, from_email, from_password]):
        raise ValueError("All parameters must be of type str")

    logging.info(f"Preparing to send email to {anonymize_email(to_email)}")

    # Create the email message
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    # Read SMTP server and port from environment variables
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))

    try:
        # Connect to the mail server using TLS
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Enable TLS encryption
            server.starttls()
            # Log in to your email account
            server.login(from_email, from_password)

            # Send the email
            server.send_message(msg)
            logging.info(f"Email sent to {anonymize_email(to_email)}")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred when sending email to {anonymize_email(to_email)}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occurred when sending email to {anonymize_email(to_email)}: {e}")
