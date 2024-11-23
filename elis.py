import smtplib
import dns.resolver
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr, make_msgid
import email.utils
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.policy import default

def load_content_from_file(file_path):
    """Read and return the content of a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def log_email_status(recipient, log_file, status):
    """Log the status of an email send attempt."""
    with open(log_file, 'a', encoding='utf-8') as file:
        file.write(f"{recipient}: {status}\n")

def resolve_mx_server(domain):
    """Resolve MX server for the given domain."""
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_record = sorted(mx_records, key=lambda rec: rec.preference)[0]
        return str(mx_record.exchange).strip('.')
    except Exception as e:
        print(f"Failed to resolve MX records for domain {domain}: {e}")
        return None

def generate_random_tracking_number():
    """Generate a random tracking number with the format of letters and numbers."""
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    numbers = '0123456789'
    tracking_number = ''.join(random.choice(letters + numbers) for _ in range(12))
    return f"UZ{tracking_number}"

def send_email(bcc_recipients, base_subject, text_message, html_file_path, sender_name, sender_email, delay=1, max_retries=3):
    """Send email to recipients with retry logic in case of specific errors."""
    # Generate random numbers for email and subject
    random_number_email = random.randint(1000, 9999)
    random_number_subject = random.randint(10000, 99999)

    # Modify the sender email and subject
    sender_email = sender_email.replace("31300", f"31300{random_number_email}")
    subject = base_subject.replace("90000", str(random_number_subject))

    # Load HTML content from file
    html_message = load_content_from_file(html_file_path)

    # Generate a random tracking number
    random_tracking_number = generate_random_tracking_number()

    # Replace the placeholder tracking number in the HTML message
    html_message = html_message.replace('UZ3USUY89', random_tracking_number)

    # Resolve MX server
    domain = bcc_recipients[0].split('@')[1]  # Assuming all recipients have the same domain
    mx_server = resolve_mx_server(domain)
    if not mx_server:
        for recipient in bcc_recipients:
            log_email_status(recipient, "failure_log.txt", "MX server resolution failed")
        return

    msg = MIMEMultipart('alternative')
    msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))
    msg['Subject'] = Header(subject, 'utf-8')

    # Add headers to bypass spam filters
    msg['Message-ID'] = make_msgid(domain=domain)
    msg['Date'] = email.utils.formatdate(localtime=True)
    msg['Return-Path'] = sender_email  # Helps with DMARC alignment
    msg['X-Priority'] = '3'  # Normal priority
    msg['X-MSMail-Priority'] = 'Normal'
    msg['List-Unsubscribe'] = f"<mailto:unsubscribe@{domain}?subject=unsubscribe>"

    msg.attach(MIMEText(text_message, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_message, 'html', 'utf-8'))

    retries = 0
    while retries < max_retries:
        try:
            # Establish connection to the MX server
            with smtplib.SMTP(mx_server) as server:
                server.set_debuglevel(0)
                server.ehlo('google.com')  # Send EHLO with the specified domain

                # Send the email without authentication
                server.sendmail(sender_email, bcc_recipients, msg.as_string())
                for recipient in bcc_recipients:
                    log_email_status(recipient, "success_log.txt", "Email sent successfully")
                print(f"Email successfully sent to {len(bcc_recipients)} recipients with subject {subject}.")
                return  # Exit if email is successfully sent
        except smtplib.SMTPRecipientsRefused as e:
            # Specific error for too many recipients
            print(f"Error: Too many recipients for {bcc_recipients}. Retrying in 10 seconds...")
            time.sleep(1)  # Wait before retrying
        except Exception as e:
            # General error handling
            print(f"Failed to send email: {e}")
            for recipient in bcc_recipients:
                log_email_status(recipient, "failure_log.txt", "Email sending failed")
            return

        retries += 1
        print(f"Retrying... Attempt {retries}/{max_retries}")
        time.sleep(1)  # Wait before retrying

    # If all retries failed
    for recipient in bcc_recipients:
        log_email_status(recipient, "failure_log.txt", "Email sending failed after retries")

def send_emails_in_batches(recipient_emails, base_subject, text_message, html_file_path, sender_name, sender_email, batch_size=1, max_workers=1, delay=0):
    """Send emails in batches and disconnect/reconnect after each batch."""
    def chunked_iterable(iterable, size):
        """Yield successive chunks from iterable of size size."""
        for i in range(0, len(iterable), size):
            yield iterable[i:i + size]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for recipients_batch in chunked_iterable(recipient_emails, batch_size):
            futures.append(executor.submit(send_email, recipients_batch, base_subject, text_message, html_file_path, sender_name, sender_email, delay))
            
            # Wait for the batch to complete, then disconnect and reconnect
            for future in as_completed(futures):
                future.result()  # Wait for each future to complete

            print("Batch sent, disconnecting and reconnecting...")

            # This is where the disconnection/reconnection happens
            time.sleep(1)  # Simulate reconnection delay before the next batch

def load_recipients_from_file(file_path):
    """Load email recipients from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines() if line.strip()]

# Example usage
recipient_emails = load_recipients_from_file("mails.txt")  # Update the path to your file
base_subject = "Sssiert?"
text_message = ""
html_file_path = "message.html"  # Update the path to your HTML file
base_sender_name = "deld"  # Change this to your name
base_sender_email = "news@lousboutiques.com"  # Replace with your base sender email

send_emails_in_batches(recipient_emails, base_subject, text_message, html_file_path, base_sender_name, base_sender_email, max_workers=1, delay=0)
