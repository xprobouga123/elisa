import smtplib
import dns.resolver
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr


def log_message(file_path, message):
    """Helper function to log success or failure messages to a file."""
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(message + "\n")


def send_email(recipients_chunk, subject, text_message, html_message,
               sender_name, sender_email, to_email):
    # Resolve MX record for the recipient's domain (based on the first recipient)
    try:
        domain = recipients_chunk[0].split('@')[1]
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_server = str(
            sorted(mx_records,
                   key=lambda rec: rec.preference)[0].exchange).strip('.')
    except Exception as e:
        error_message = f"Failed to resolve MX record for {recipients_chunk[0]}: {e}"
        log_message("failure_log.txt", error_message)
        print(error_message)
        return

    # Create the email message
    msg = MIMEMultipart('alternative')
    msg['From'] = formataddr((sender_name, sender_email))
    msg['To'] = to_email  # Always fixed
    msg['Subject'] = subject

    # Attach plain text and HTML versions of the email
    msg.attach(MIMEText(text_message, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_message, 'html', 'utf-8'))

    # Send the email
    try:
        with smtplib.SMTP(mx_server) as server:
            server.sendmail(sender_email, recipients_chunk, msg.as_string())
        success_message = f"Email sent to {len(recipients_chunk)} recipients in BCC"
        log_message("success_log.txt", success_message)
        print(success_message)
    except Exception as e:
        error_message = f"Failed to send email to BCC chunk: {e}"
        log_message("failure_log.txt", error_message)
        print(error_message)


# Load recipients from a file
def load_recipients(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]


# Load the content of a file
def load_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


# Helper function to chunk the recipient list
def chunk_recipients(recipients, chunk_size):
    for i in range(0, len(recipients), chunk_size):
        yield recipients[i:i + chunk_size]


# Example usage
recipients = load_recipients("mails.txt")  # List of recipients from file
text_message = load_content("message.txt")  # Plain text message from file
html_message = load_content("black.html")  # HTML message from file
subject = "Uskollisille Asiakkaillemme: Erikoistarjous Black Fridayna!"
sender_name = "Elisa"
sender_email = "elisa.promo@b.fi"
to_email = "elisa.promo@b.fi"  # Fixed "To" email address

# Process recipients in chunks of 50
for recipient_chunk in chunk_recipients(recipients, 10):
    send_email(recipient_chunk, subject, text_message, html_message,
               sender_name, sender_email, to_email)
