from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class CartItem(BaseModel):
    id: str
    name: str
    price: float = Field(..., gt=0)
    quantity: int = Field(default=1, ge=1)


class CustomerAddress(BaseModel):
    street: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str = "US"


class PaymentDetails(BaseModel):
    card_number_masked: str = "**** **** **** 4242"
    exp_month: int = 12
    exp_year: int = 2028


class CheckoutRequest(BaseModel):
    cart_items: List[CartItem]
    shipping_address: CustomerAddress
    payment_details: Optional[PaymentDetails] = None
    coupon_code: Optional[str] = None


class CheckoutResponse(BaseModel):
    order_id: str
    subtotal: float
    tax: float
    total: float
    currency: str = "USD"
    status: str = "COMPLETED"
    deployment_version: str
    message: str


class IncidentPayload(BaseModel):
    incident_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    service: str = "checkout-backend"
    deployment_version: str
    environment: str = "production"
    error_type: str
    error_message: str
    stack_trace: str
    endpoint: str = "/api/checkout"
    request_payload: Dict[str, Any]
    status: str = "TRIGGERED"  # TRIGGERED, INVESTIGATING, FIXING, VERIFIED, RESOLVED, FAILED


class HealthResponse(BaseModel):
    status: str
    service: str = "checkout-backend"
    version: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
