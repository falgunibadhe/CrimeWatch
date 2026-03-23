# backend/main.py

import os
import datetime
import base64
import smtplib
from email.message import EmailMessage
from collections import defaultdict, deque

import torch
import numpy as np
import cv2
from PIL import Image
from torchvision import transforms
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from pymongo import MongoClient
from dotenv import load_dotenv
from ultralytics import YOLO
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware


from .models import CNN_LSTM
from .auth_router import router as auth_router

# =====================================================
# APP
# =====================================================

app = FastAPI(title="CrimeWatch API")
app.include_router(auth_router)


# CORS so React can call FastAPI
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"  # you can remove "*" later and keep only the ones you use
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers=["*"],
)

# =====================================================
# CONFIG
# =====================================================

load_dotenv()

ALERT_EMAIL = os.getenv("ALERT_EMAIL")
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


def pil_from_bgr(bgr):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def predict_violence_from_buffer(buffer_deque):
    try:
        tensors = [transform(pil_from_bgr(f)) for f in list(buffer_deque)]
        clip = torch.stack(tensors).unsqueeze(0).to(device)
        with torch.no_grad():
            out = violence_model(clip)
            prob = float(out.squeeze().cpu().item())
        label = "Violence" if prob >= 0.5 else "Non-Violence"
        return label, prob
    except Exception as e:
        print("❌ Violence prediction error:", e)
        return "Error", 0.0


def detect_weapons_in_frame(frame, conf_threshold=0.5):
    try:
        results = weapon_model.predict(frame, conf=conf_threshold, verbose=False)
        boxes = results[0].boxes

        if boxes is not None:
            print("🧠 YOLO classes:", boxes.cls.tolist())

        weapon_boxes = []
        if boxes is not None and len(boxes) > 0:
            for box, cls in zip(boxes.xyxy, boxes.cls):
                x1, y1, x2, y2 = map(int, box.tolist())
                weapon_boxes.append([x1, y1, x2, y2])

        return weapon_boxes
    except Exception as e:
        print("❌ YOLO error:", e)
        return []


def send_email_alert(location: str, dt: str, file_path: str, danger_label: str):
    try:
        if not GMAIL_EMAIL or not ALERT_EMAIL or not GMAIL_APP_PASSWORD:
            print("⚠️ Gmail config missing.")
            return {"status": "disabled"}

        msg = EmailMessage()
        msg["Subject"] = f"🚨 CrimeWatch Alert: {danger_label}"
        msg["From"] = GMAIL_EMAIL
        msg["To"] = ALERT_EMAIL

        msg.set_content(
            f"""
Crime Detected!

Type: {danger_label}
Location: {location}
Time: {dt}

Snapshot attached.
"""
        )

        with open(file_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(file_path)

        msg.add_attachment(
            file_data,
            maintype="image",
            subtype="png",
            filename=file_name,
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        print("✅ Gmail alert sent successfully")
        return {"status": "sent"}

    except Exception as e:
        print("❌ Gmail error:", e)
        return {"status": "error", "message": str(e)}

# =====================================================
# CORE LOGIC
# =====================================================

async def process_frame(frame: UploadFile, camera_id: str):
    content = await frame.read()
    nparr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "Invalid image"}

    print("📸 Frame received:", img.shape)

    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    location = camera_id

    # Weapon detection
    weapon_boxes = detect_weapons_in_frame(img)
    weapon_detected = len(weapon_boxes) > 0
    print("🔫 Weapon boxes:", weapon_boxes)

    # Violence detection
    buf = frame_buffers[camera_id]
    buf.append(img.copy())

    violence_label, violence_prob = ("NotEnoughFrames", 0.0)
    if len(buf) == SEQ_LEN:
        violence_label, violence_prob = predict_violence_from_buffer(buf)

    print("⚔️ Violence:", violence_label, violence_prob)

    danger = weapon_detected or violence_label == "Violence"
    danger_label = "Violence/Weapon" if danger else "Safe"
    print("🚨 FINAL DANGER:", danger_label)

    snapshot_path = None
    email_status = {"status": "none"}

    if danger:
        basename = f"alert_{camera_id}_{int(datetime.datetime.now().timestamp())}.png"
        snapshot_path = os.path.join(TEMP_DIR, basename)
        cv2.imwrite(snapshot_path, img)
        email_status = send_email_alert(location, dt, snapshot_path, danger_label)

    alerts_collection.insert_one({
        "timestamp": dt,
        "camera_id": camera_id,
        "danger_status": danger_label,
        "violence_label": violence_label,
        "violence_prob": violence_prob,
        "weapon_detected": weapon_detected,
        "snapshot_path": snapshot_path,
        "email_status": email_status,
    })

    return {"message": "Frame processed", "status": danger_label}

# =====================================================
# API ROUTES
# =====================================================

@app.post("/upload-frame")
async def upload_frame_endpoint(
    frame: UploadFile = File(...),
    camera_id: str = Form("camera_01")
):
    return await process_frame(frame, camera_id)


@app.get("/alerts")
def get_alerts_endpoint(limit: int = 20):
    docs = list(
        alerts_collection.find({}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )
    return {"alerts": docs}


@app.get("/snapshot/{filename}")
def get_snapshot_endpoint(filename: str):
    path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(path):
        return {"error": "File not found."}
    return FileResponse(path, media_type="image/png")


@app.get("/")
def root():
    return {"message": "CrimeWatch backend running ✅"}
