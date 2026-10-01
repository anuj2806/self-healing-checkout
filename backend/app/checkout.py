import os
import uuid
import logging
import importlib
from fastapi import HTTPException

from app.models import CheckoutRequest, CheckoutResponse
import app.tax
from app.incident import emit_incident

logger = logging.getLogger("checkout_service")


def process_checkout(request: CheckoutRequest) -> CheckoutResponse:
    """
    Executes checkout workflow: subtotal calculation, tax computation,
    and simulated payment execution.
    If an unhandled exception occurs, an incident is emitted.
    """
    current_version = os.getenv("APP_VERSION", "v1.0.0")

    if not request.cart_items:
        raise HTTPException(status_code=400, detail="Cart cannot be empty")

    subtotal = sum(item.price * item.quantity for item in request.cart_items)

    try:
        # Dynamically reload tax module to immediately pick up any autonomous patches merged to main
        importlib.reload(app.tax)
        tax_amount = app.tax.calculate_tax(
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
            deployment_version=current_version,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Checkout Processing Failed",
                "incident_id": incident.incident_id,
                "error_type": incident.error_type,
                "error_message": incident.error_message,
                "deployment_version": current_version,
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
        deployment_version=current_version,
        message="Order placed successfully!",
    )
