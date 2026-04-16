from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List


# -----------------------------
# Signup Schema
# -----------------------------
class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


# -----------------------------
# Login Schema
# -----------------------------
class UserLogin(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


# -----------------------------
# Token Schema (JWT Response)
# -----------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# -----------------------------
# Token Payload (Internal Use)
# -----------------------------
class TokenData(BaseModel):
    username: Optional[str] = None


# -----------------------------
# Email Registration Schema
# -----------------------------
class EmailRegister(BaseModel):
    email1: EmailStr
    email2: Optional[EmailStr] = None


# -----------------------------
# User Output Schema (Response)
# -----------------------------
class UserOut(BaseModel):
    id: str
    full_name: str
    username: str
    email: EmailStr
    alternate_emails: Optional[List[EmailStr]] = None

    class Config:
        from_attributes = True


# -----------------------------
# Generic Message Response
# -----------------------------
class MessageResponse(BaseModel):
    message: str