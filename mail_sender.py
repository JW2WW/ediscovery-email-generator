import smtplib
import random
import configparser
import time
import io
from email.utils import formatdate
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from email.generator import BytesGenerator
from email.policy import SMTP  # <-- CRITICAL: Import the strict SMTP wire policy
from faker import Faker

fake = Faker()

def generate_fake_email():
    return fake.email()

def _load_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config

def load_smtp_config():
    config = _load_config()
    host = config.get("smtp", "host", fallback="localhost")
    port = config.getint("smtp", "port", fallback=1025)
    return host, port

def load_date_settings():
    """Return (randomize_date, range_years_back) from config."""
    config = _load_config()
    randomize = config.getboolean("dates", "randomize_date", fallback=True)
    years_back = config.getint("dates", "range_years_back", fallback=10)
    return randomize, max(years_back, 0)

def get_message_timestamp():
    """Return a Unix timestamp for the email Date header."""
    randomize, years_back = load_date_settings()
    if not randomize:
        return int(time.time())
    now = int(time.time())
    start_time = now - (years_back * 365 * 24 * 60 * 60)
    return random.randint(start_time, now)

def build_custom_email(subject, body_text, attachments=None):
    # CRITICAL FIX: Assign the strict SMTP policy directly to the message object upon creation.
    # This forces every sub-boundary and component to respect the 76-character line wrap.
    msg = MIMEMultipart('mixed', policy=SMTP)
    
    msg['Subject'] = subject
    msg['From'] = generate_fake_email()
    msg['To'] = generate_fake_email()
    
    msg['Date'] = formatdate(get_message_timestamp(), localtime=True)
    
    if random.random() > 0.5:
        msg['Cc'] = generate_fake_email()

    # Apply SMTP policy to the inner container as well
    body_container = MIMEMultipart('alternative', policy=SMTP)
    text_part = MIMEText(body_text, 'plain', 'utf-8')
    
    # We force Base64 on the text layer to ensure it folds perfectly
    text_part.replace_header('Content-Transfer-Encoding', 'base64')
    encoders.encode_base64(text_part)
        
    body_container.attach(text_part)
    msg.attach(body_container)

    if attachments:
        for attachment in attachments:
            if attachment:
                # Ensure the attachment sub-part inherits the strict wrapping rule
                attachment.policy = SMTP
                msg.attach(attachment)
                
    return msg

def transmit_email(msg):
    host, port = load_smtp_config()
    recipients = [msg['To']]
    if msg.get('Cc'):
        recipients.append(msg['Cc'])
        
    try:
        # Build the byte stream directly using our strict SMTP policy rules
        buffer = io.BytesIO()
        generator = BytesGenerator(buffer, policy=SMTP)
        generator.flatten(msg)
        safe_message_bytes = buffer.getvalue()
        
        with smtplib.SMTP(host, port) as server:
            server.sendmail(msg['From'], recipients, safe_message_bytes)
        return True
    except Exception as e:
        print(f"SMTP Transmission Failed to {host}:{port} -> {e}")
        return False
