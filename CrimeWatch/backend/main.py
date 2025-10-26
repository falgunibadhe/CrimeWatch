import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
import datetime
from database import alerts_collection  # MongoDB collection

load_dotenv()
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

last_alert_time = None
ALERT_COOLDOWN = 60  # seconds

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_VIDEO_DIR = "temp_videos"
os.makedirs(TEMP_VIDEO_DIR, exist_ok=True)

# --- SendGrid Email with Attachment ---
def send_email_alert(location: str, dt: str, file_path: str):
    with open(file_path, "rb") as f:
        encoded_file = base64.b64encode(f.read()).decode()

    attachment = Attachment(
        file_content=FileContent(encoded_file),
        file_type=FileType("image/png"),
        file_name=FileName(os.path.basename(file_path)),
        disposition=Disposition("attachment")
    )

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=ALERT_EMAIL,
        subject="Crime Alert!",
        html_content=f"Suspicious activity detected at {location} on {dt}"
    )
    message.attachment = attachment

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return {"status": "sent", "code": response.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def send_email_if_cooldown(location, dt, file_path):
    global last_alert_time
    now = datetime.datetime.now()
    if last_alert_time and (now - last_alert_time).total_seconds() < ALERT_COOLDOWN:
        return {"status": "skipped_cooldown"}
    last_alert_time = now
    return send_email_alert(location, dt, file_path)

# --- Placeholder Detection ---
def placeholder_detection(video_path: str):
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "suspicious": True,
        "location": "Camera 01",
        "datetime": dt,
        "details": "Simulated weapon detection"
    }

@app.post("/upload-video/")
async def analyze_video(video: UploadFile = File(...)):
    temp_file_path = os.path.join(TEMP_VIDEO_DIR, f"{datetime.datetime.now().timestamp()}_{video.filename}")
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    video.file.close()

    analysis_result = placeholder_detection(temp_file_path)

    if analysis_result["suspicious"]:
        email_status = send_email_if_cooldown(
            location=analysis_result["location"],
            dt=analysis_result["datetime"],
            file_path=temp_file_path
        )
    else:
        email_status = {"status": "no_alert"}

    # Save to MongoDB
    alerts_collection.insert_one({
        "timestamp": analysis_result["datetime"],
        "location": analysis_result["location"],
        "details": analysis_result["details"],
        "snapshot_path": temp_file_path,
        "email_status": email_status
    })

    return {
        "status": "processed",
        "details": analysis_result,
        "email_status": email_status
    }

@app.get("/")
def read_root():
    return {"message": "CrimeWatch API running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
