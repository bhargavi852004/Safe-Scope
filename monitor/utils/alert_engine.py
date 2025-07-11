import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_parent_alert(log):
    """
    Sends an alert email to the parent when risky content is detected.
    """

    if log.label.lower() != "risky":
        return  # Do nothing if not risky

    sender_email = settings.EMAIL_HOST_USER
    receiver_email = log.parent_email
    password = settings.EMAIL_HOST_PASSWORD

    if not receiver_email:
        logger.error("❌ Cannot send alert: Parent email is None.")
        return

    subject = f"⚠️ Risky Activity Detected: {log.title}"
    body = f"""
🚨 A risky website interaction has been detected for your child:

📌 URL: {log.url}
📄 Title: {log.title}
⏰ Time: {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
🧠 Verdict: {log.label.upper()} — {log.reason}
📝 Summary:
{log.summary}

Please review their activity on the SafeScope dashboard.

Stay alert. Stay safe.  
🛡️ SafeScope Team
    """

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)
            logger.info(f"✅ Alert email sent to {receiver_email}")
    except Exception as e:
        logger.error(f"❌ Failed to send email alert: {e}")
