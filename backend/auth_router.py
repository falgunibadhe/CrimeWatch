from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from . import auth_schemas, auth_utils

USER_COLLECTION = auth_utils.USER_COLLECTION
router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")

SECRET_KEY = auth_utils.SECRET_KEY
ALGORITHM = auth_utils.ALGORITHM


# -----------------------------
# Get Current User (JWT Verify)
# -----------------------------
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        user = USER_COLLECTION.find_one({"username": username})

        if not user:
            raise credentials_exception

        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "alternate_emails": user.get("alternate_emails", [])
        }

    except JWTError:
        raise credentials_exception


# -----------------------------
# Verify Token
# -----------------------------
@router.get("/verify")
def verify_token(current_user: dict = Depends(get_current_user)):
    return {
        "status": "valid",
        "username": current_user["username"],
        "email": current_user["email"]
    }


# -----------------------------
# Signup
# -----------------------------
@router.post("/signup", response_model=auth_schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user: auth_schemas.UserCreate):

    if USER_COLLECTION.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")

    if USER_COLLECTION.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = auth_utils.get_password_hash(user.password)

    new_user = {
        "full_name": user.full_name,
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "alternate_emails": []  # ✅ initialize
    }

    result = USER_COLLECTION.insert_one(new_user)

    return {
        "id": str(result.inserted_id),
        "full_name": user.full_name,
        "username": user.username,
        "email": user.email,
        "alternate_emails": []
    }


# -----------------------------
# Signin
# -----------------------------
@router.post("/signin", response_model=auth_schemas.Token)
def login_for_access_token(user_data: auth_schemas.UserLogin):

    user_doc = USER_COLLECTION.find_one({"username": user_data.username})

    if not user_doc or not auth_utils.verify_password(
        user_data.password, user_doc["hashed_password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_utils.create_access_token(
        data={"sub": user_doc["username"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# -----------------------------
# Register Alternate Emails ✅
# -----------------------------
@router.post("/register-emails", response_model=auth_schemas.MessageResponse)
def register_emails(
    data: auth_schemas.EmailRegister,
    current_user: dict = Depends(get_current_user)
):
    """
    Add/update alternate emails for logged-in user
    """

    # Validation
    if data.email1 == data.email2:
        raise HTTPException(
            status_code=400,
            detail="Emails cannot be the same"
        )

    email_list = [data.email1]
    if data.email2:
        email_list.append(data.email2)

    result = USER_COLLECTION.update_one(
        {"username": current_user["username"]},
        {"$set": {"alternate_emails": email_list}}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Failed to update emails"
        )

    return {"message": "Emails registered successfully"}