from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .models import UserCreate, Token, InvoiceData
from .auth import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from .db import get_user, create_user, create_audit_log, get_audit_logs, update_user, supabase
from .services import process_invoice, get_num_pages
import os
from typing import Optional
from datetime import datetime, UTC
import secrets
from dotenv import load_dotenv

load_dotenv()

settings = get_settings()
app = FastAPI(title=settings.PROJECT_NAME)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user(payload.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_user_api_key(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Find user by API key
    response = supabase.table("users").select("*").eq("api_key", x_api_key).execute()
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = response.data[0]
    
    # Update last used timestamp
    await update_user(user["id"], {
        "api_key_last_used": datetime.now(UTC)
    })
    
    return user

@app.post(f"{settings.API_V1_STR}/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    if await get_user(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_dict = user_data.dict()
    user_dict["hashed_password"] = get_password_hash(user_data.password)
    user_dict["created_at"] = datetime.now(UTC)
    user_dict["updated_at"] = datetime.now(UTC)
    
    user = await create_user(user_dict)
    
    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post(f"{settings.API_V1_STR}/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post(f"{settings.API_V1_STR}/auth/generate-api-key")
async def generate_api_key(current_user: dict = Depends(get_current_user)):
    # Generate a new API key
    api_key = secrets.token_urlsafe(32)
    
    # Update user with new API key
    await update_user(current_user["id"], {
        "api_key": api_key,
        "api_key_created_at": datetime.now(UTC),
        "api_key_last_used": None
    })
    
    return {"api_key": api_key}

@app.post(f"{settings.API_V1_STR}/auth/revoke-api-key")
async def revoke_api_key(current_user: dict = Depends(get_current_user)):
    # Revoke API key by setting it to None
    await update_user(current_user["id"], {
        "api_key": None,
        "api_key_created_at": None,
        "api_key_last_used": None
    })
    
    return {"message": "API key revoked successfully"}

@app.post(f"{settings.API_V1_STR}/process-invoice", response_model=InvoiceData)
async def process_invoice_endpoint(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_api_key)
):
    # Validate file type
    file_type = file.filename.split(".")[-1].lower()
    if file_type not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Read file content
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
        )
    
    # Process invoice
    invoice_data, error, tokens_used = await process_invoice(
        content,
        file_type,
        file.filename,
        len(content)
    )
    
    # Create audit log
    await create_audit_log({
        "user_id": current_user["id"],
        "api_key": current_user.get("api_key", ""),
        "file_name": file.filename,
        "file_size": len(content),
        "num_pages": get_num_pages(content, file_type),
        "tokens_used": tokens_used,
        "status": "success" if invoice_data else "error",
        "created_at": datetime.now(UTC),
        "input_data": {"file_name": file.filename, "file_size": len(content)},
        "output_data": invoice_data.dict() if invoice_data else None,
        "error_message": error
    })
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return invoice_data

@app.get(f"{settings.API_V1_STR}/audit-logs")
async def get_user_audit_logs(
    current_user: dict = Depends(get_current_user),
    limit: int = 100
):
    logs = await get_audit_logs(current_user["id"], limit)
    return logs 