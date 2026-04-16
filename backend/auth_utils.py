import os
import datetime
from datetime import timedelta, timezone
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from pymongo import MongoClient
from dotenv import load_dotenv

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY not set in environment variables")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# -----------------------------
# MongoDB Setup
# -----------------------------
try:
    client = MongoClient(MONGODB_URI)
    db = client["crimewatch"]
    USER_COLLECTION = db["users"]

    # Ensure unique indexes
    USER_COLLECTION.create_index("username", unique=True)
    USER_COLLECTION.create_index("email", unique=True)

except Exception as e:
    raise Exception(f"Database connection failed: {e}")


# -----------------------------
# Security Setup
# -----------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")


# -----------------------------
# Password Functions
# -----------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# -----------------------------
# Token Creation
# -----------------------------
def create_access_token(data: dict) -> str:
    """
    Generates JWT token with expiry and standard claims
    """
    to_encode = data.copy()

    now = datetime.datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "access"  # ✅ added (important for scaling)
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -----------------------------
# Token Decode Utility
# -----------------------------
def decode_access_token(token: str) -> dict:
    """
    Decodes JWT token and returns payload
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Optional: enforce token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )