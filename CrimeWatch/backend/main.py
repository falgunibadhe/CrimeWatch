from fastapi import FastAPI, UploadFile, File
from datetime import datetime
import shutil
from alert import send_email_alert

app = FastAPI()

@app.get("/test-alert/")
def test_alert():
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = send_email_alert("Main Gate", dt)
    return {"test_time": dt, "email_result": result}

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Dummy detection
    crime_detected = True
    label = "Suspicious activity"

    if crime_detected:
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        email_result = send_email_alert("Main Gate", dt)
    else:
        email_result = {"status": "no_alert"}

    return {
        "status": "processed",
        "label": label,
        "alert": crime_detected,
        "email_result": email_result
    }
