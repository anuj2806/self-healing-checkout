import os
import uuid
import logging
from fastapi import HTTPException

from app.models import CheckoutRequest, CheckoutResponse
from app.tax import calculate_tax
from app.incident import emit_incident

logger = logging.getLogger("checkout_service")
CURRENT_VERSION = os.getenv("APP_VERSION", "v1.0.0")


def process_checkout(request: CheckoutRequest) -> CheckoutResponse:
    """
    Executes checkout workflow: subtotal calculation, tax computation,
    and simulated payment execution.
    If an unhandled exception occurs, an incident is emitted.
    """
    if not request.cart_items:
        raise HTTPException(status_code=400, detail="Cart cannot be empty")

    subtotal = sum(item.price * item.quantity for item in request.cart_items)

    try:
        # Calculates tax based on destination jurisdiction
        # In v1.0.0, this triggers an unhandled KeyError for unlisted US states (e.g., 'FL')
        tax_amount = calculate_tax(
            subtotal=subtotal,
            country=request.shipping_address.country,
            state=request.shipping_address.state,
        )
    except Exception as e:
        logger.exception(f"Checkout tax computation failed for country={request.shipping_address.country}, state={request.shipping_address.state}")
        # Capture error, build structured incident, and emit
        incident = emit_incident(
            error=e,
            request_payload=request.model_dump(),
            endpoint="/api/checkout",
            deployment_version=CURRENT_VERSION,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Checkout Processing Failed",
                "incident_id": incident.incident_id,
                "error_type": incident.error_type,
                "error_message": incident.error_message,
                "deployment_version": CURRENT_VERSION,
            },
        )

    total = round(subtotal + tax_amount, 2)
    order_id = f"ord-{uuid.uuid4().hex[:8]}"

    return CheckoutResponse(
        order_id=order_id,
        subtotal=round(subtotal, 2),
        tax=tax_amount,
        total=total,
        currency="USD",
        status="COMPLETED",
        deployment_version=CURRENT_VERSION,
        message="Order placed successfully!",
    )
