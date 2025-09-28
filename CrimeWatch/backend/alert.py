from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from dotenv import load_dotenv

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

def send_email_alert(location: str, dt: str):
    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=ALERT_EMAIL,
        subject='Crime Alert!',
        html_content=f"Suspicious activity detected at {location} on {dt}"
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return {"status": "sent", "code": response.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}
