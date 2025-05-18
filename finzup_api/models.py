from pydantic import BaseModel, EmailStr, Field
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
    street: str = Field(..., description="Street address of the entity")
    city: str = Field(..., description="City where the entity is located")
    phone: Optional[str] = Field(None, description="Phone number of the entity")
    fax: Optional[str] = Field(None, description="Fax number of the entity")
    email: Optional[EmailStr] = Field(None, description="Email address of the entity")
    license: Optional[str] = Field(None, description="Business license number of the entity")

class Supplier(BaseModel):
    name: str = Field(..., description="Name of the supplier or vendor")
    address: Address = Field(..., description="Address information of the supplier")

class Recipient(BaseModel):
    name: str = Field(..., description="Name of the recipient or customer")
    address: Address = Field(..., description="Address information of the recipient")

class DeliveryCompany(BaseModel):
    name: str = Field(..., description="Name of the delivery company")
    phone: str = Field(..., description="Phone number of the delivery company")
    email: Optional[EmailStr] = Field(None, description="Email address of the delivery company")
    notes: Optional[str] = Field(None, description="Additional notes about the delivery")

class InvoiceItem(BaseModel):
    description: str = Field(..., description="Description of the item or service")
    quantity: int = Field(..., description="Quantity of the item", ge=1)
    unitPriceNis: float = Field(..., description="Unit price in NIS (New Israeli Shekel)", ge=0)
    totalPriceNis: float = Field(..., description="Total price for the item in NIS", ge=0)
    barcode: Optional[str] = Field(None, description="Barcode or product code of the item")

class InvoiceData(BaseModel):
    invoiceNumber: int = Field(..., description="Unique invoice number", ge=1)
    invoiceDate: str = Field(..., description="Date of the invoice")
    supplier: Supplier = Field(..., description="Information about the supplier")
    recipient: Recipient = Field(..., description="Information about the recipient")
    delivery_company: Optional[DeliveryCompany] = Field(None, description="Information about the delivery company")
    items: List[InvoiceItem] = Field(..., description="List of items or services in the invoice", min_items=1)
    totalAmountNis: float = Field(..., description="Total amount of the invoice in NIS", ge=0) 