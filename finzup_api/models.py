from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    api_key: Optional[str] = None
    api_key_created_at: Optional[datetime] = None
    api_key_last_used: Optional[datetime] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDB(UserBase):
    id: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    exp: int

class AuditLog(BaseModel):
    id: str
    user_id: str
    api_key: str
    file_name: str
    file_size: int
    num_pages: int
    tokens_used: int
    status: str
    created_at: datetime
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None

# Invoice Data Models
class Address(BaseModel):
    street: str
    city: str
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    license: Optional[str] = None

class Supplier(BaseModel):
    name: str
    address: Address

class Recipient(BaseModel):
    name: str
    address: Address

class InvoiceItem(BaseModel):
    description: str
    quantity: int
    unitPriceNis: float
    totalPriceNis: float
    barcode: Optional[str] = None

class InvoiceData(BaseModel):
    invoiceNumber: int
    invoiceDate: str
    supplier: Supplier
    recipient: Recipient
    items: List[InvoiceItem]
    totalAmountNis: float 