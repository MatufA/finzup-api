from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .models import InvoiceData
from .db import create_audit_log, get_audit_logs, update_user, supabase
from .services import process_invoice, get_num_pages, ProcessInvoiceResponse
import os
from datetime import datetime, UTC

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

@app.post(f"{settings.API_V1_STR}/process-invoice", response_model=InvoiceData)
async def process_invoice_endpoint(
    file: UploadFile = File(...)
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
    result = await process_invoice(
        content,
        file_type,
        file.filename,
        len(content)
    )
    
    # Create audit log (user_id and api_key are omitted)
    await create_audit_log({
        "user_id": None,
        "api_key": None,
        "file_name": file.filename,
        "file_size": len(content),
        "num_pages": get_num_pages(content, file_type),
        "tokens_used": result.usage_metadata.get("total_tokens", -1),
        "status": "success" if result.invoice_data else "error",
        "created_at": datetime.now(UTC),
        "input_data": {"file_name": file.filename, "file_size": len(content)},
        "output_data": result.invoice_data.model_dump() if result.invoice_data else None,
        "error_message": result.error
    })
    
    if result.error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
    
    return result.invoice_data

@app.get(f"{settings.API_V1_STR}/audit-logs")
async def get_user_audit_logs(
    limit: int = 100
):
    logs = await get_audit_logs(None, limit)
    return logs 