# backend/main.py

import os
import datetime
import smtplib
from email.message import EmailMessage
from collections import defaultdict, deque

import torch
import numpy as np
import cv2
from PIL import Image
from torchvision import transforms
from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from pymongo import MongoClient
from dotenv import load_dotenv
from ultralytics import YOLO
from fastapi.middleware.cors import CORSMiddleware

from .models import CNN_LSTM
from .auth_router import router as auth_router, get_current_user

# =====================================================
# APP
# =====================================================

app = FastAPI(title="CrimeWatch API")
app.include_router(auth_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# CONFIG
# =====================================================

load_dotenv()

GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

MODEL_WEAPON_PATH = "backend\\best.pt"
MODEL_VIOLENCE_PATH = "backend\\cnn_lstm.pth"
TEMP_DIR = "backend\\temp_snapshots"
os.makedirs(TEMP_DIR, exist_ok=True)

SEQ_LEN = int(os.getenv("SEQ_LEN", "16"))

# =====================================================
# DATABASE
# =====================================================

client = MongoClient(MONGODB_URI)
db = client["crimewatch"]
alerts_collection = db["alerts"]

# =====================================================
# MODELS
# =====================================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

print("🔁 Loading models...")

weapon_model = YOLO(MODEL_WEAPON_PATH)

violence_model = CNN_LSTM()
violence_state = torch.load(MODEL_VIOLENCE_PATH, map_location=device)
clean_state = {k.replace("module.", ""): v for k, v in violence_state.items()}
violence_model.load_state_dict(clean_state)
violence_model.to(device)
violence_model.eval()

print("✅ Models loaded successfully.")

# =====================================================
# HELPERS
# =====================================================

frame_buffers = defaultdict(lambda: deque(maxlen=SEQ_LEN))
last_alert_time = {}

def pil_from_bgr(bgr):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def predict_violence_from_buffer(buffer_deque):
    tensors = [transform(pil_from_bgr(f)) for f in list(buffer_deque)]
    clip = torch.stack(tensors).unsqueeze(0).to(device)
    with torch.no_grad():
        out = violence_model(clip)
        prob = float(out.squeeze().cpu().item())
    label = "Violence" if prob >= 0.5 else "Non-Violence"
    return label, prob


def detect_weapons_in_frame(frame):
    results = weapon_model.predict(frame, conf=0.5, verbose=False)
    boxes = results[0].boxes

    weapon_boxes = []
    if boxes is not None:
        for box in boxes.xyxy:
            weapon_boxes.append(list(map(int, box.tolist())))

    return weapon_boxes


def send_email_alert(to_email, location, dt, file_path, danger_label):
    try:
        msg = EmailMessage()
        msg["Subject"] = f"🚨 CrimeWatch Alert: {danger_label}"
        msg["From"] = GMAIL_EMAIL
        msg["To"] = to_email

        msg.set_content(f"""
Crime Detected!

Type: {danger_label}
Location: {location}
Time: {dt}

Snapshot attached.
""")

        with open(file_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="image",
                subtype="png",
                filename=os.path.basename(file_path)
            )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        return {"status": "sent"}

    except Exception as e:
        print("Email error:", e)
        return {"status": "error"}


# =====================================================
# CORE LOGIC
# =====================================================

async def process_frame(frame, camera_id, current_user):
    content = await frame.read()
    img = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "Invalid image"}

    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Detection
    weapon_boxes = detect_weapons_in_frame(img)
    weapon_detected = len(weapon_boxes) > 0

    buf = frame_buffers[camera_id]
    buf.append(img.copy())

    violence_label, violence_prob = ("NotEnoughFrames", 0.0)
    if len(buf) == SEQ_LEN:
        violence_label, violence_prob = predict_violence_from_buffer(buf)

    danger = weapon_detected or violence_label == "Violence"
    danger_label = "Violence/Weapon" if danger else "Safe"

    snapshot_path = None
    email_status = {"status": "none"}

    if danger:
        now_ts = datetime.datetime.now().timestamp()

        # Cooldown (30 sec)
        if camera_id not in last_alert_time or now_ts - last_alert_time[camera_id] > 30:
            last_alert_time[camera_id] = now_ts

            filename = f"alert_{camera_id}_{int(now_ts)}.png"
            snapshot_path = os.path.join(TEMP_DIR, filename)
            cv2.imwrite(snapshot_path, img)

            # Send to all emails
            emails = [current_user["email"]] + current_user.get("alternate_emails", [])

            for email in emails:
                send_email_alert(email, camera_id, dt, snapshot_path, danger_label)

    # Save alert
    alerts_collection.insert_one({
        "timestamp": dt,
        "camera_id": camera_id,
        "danger_status": danger_label,
        "violence_label": violence_label,
        "violence_prob": violence_prob,
        "weapon_detected": weapon_detected,
        "snapshot_path": snapshot_path,
    })

    return {"status": danger_label}


# =====================================================
# ROUTES
# =====================================================

@app.post("/upload-frame")
async def upload_frame_endpoint(
    frame: UploadFile = File(...),
    camera_id: str = Form("camera_01"),
    current_user: dict = Depends(get_current_user)
):
    return await process_frame(frame, camera_id, current_user)


@app.get("/alerts")
def get_alerts(limit: int = 20):
    return list(alerts_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))


@app.get("/snapshot/{filename}")
def get_snapshot(filename: str):
    path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(path):
        return {"error": "Not found"}
    return FileResponse(path)


@app.get("/")
def root():
    return {"message": "CrimeWatch backend running ✅"}