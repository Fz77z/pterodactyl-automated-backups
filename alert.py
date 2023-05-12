import smtplib
from email.message import EmailMessage

def send_email(subject, body, to_email, from_email, from_password):
    # Create the email message
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    # Connect to the mail server using TLS
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        # Enable TLS encryption
        server.starttls()
        # Log in to your email account
        server.login(from_email, from_password)

        # Send the email
        server.send_message(msg)



