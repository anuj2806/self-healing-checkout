from fastapi.testclient import TestClient
import pytest
from types import SimpleNamespace
from unittest.mock import Mock

from app.main import app
from app.tax import calculate_tax

client = TestClient(app)


def test_regression_inc_aab7c41b_unlisted_state_checkout(monkeypatch):
    """The exact FA incident request completes using the default US rate."""
    emit_incident = Mock(return_value=SimpleNamespace(
        incident_id="inc-aab7c41b",
        error_type="KeyError",
        error_message="'FA'",
    ))
    monkeypatch.setattr("app.checkout.emit_incident", emit_incident)
    payload = {
        "cart_items": [
            {"id": "item-101", "name": "Cyberpunk Mechanical Keyboard", "price": 120.0, "quantity": 1},
            {"id": "item-102", "name": "Precision Wireless Mouse", "price": 45.0, "quantity": 1},
        ],
        "shipping_address": {
            "street": "742 Evergreen Terrace",
            "city": "San Francisco",
            "state": "FA",
            "postal_code": "94103",
            "country": "US",
        },
        "payment_details": {
            "card_number_masked": "•••• •••• •••• 4242",
            "exp_month": 10,
            "exp_year": 2028,
        },
        "coupon_code": None,
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["subtotal"] == 165.0
    assert data["tax"] == 10.31
    assert data["total"] == 175.31
    emit_incident.assert_not_called()


def test_regression_inc_8ca91891_unlisted_state_checkout(monkeypatch):
    """The exact FA incident request completes using the default US rate."""
    emit_incident = Mock(return_value=SimpleNamespace(
        incident_id="inc-8ca91891",
        error_type="KeyError",
        error_message="'FA'",
    ))
    monkeypatch.setattr("app.checkout.emit_incident", emit_incident)
    payload = {
        "cart_items": [
            {"id": "item-101", "name": "Cyberpunk Mechanical Keyboard", "price": 120.0, "quantity": 1},
            {"id": "item-102", "name": "Precision Wireless Mouse", "price": 45.0, "quantity": 1},
        ],
        "shipping_address": {
            "street": "742 Evergreen Terrace",
            "city": "San Francisco",
            "state": "FA",
            "postal_code": "94103",
            "country": "US",
        },
        "payment_details": {
            "card_number_masked": "•••• •••• •••• 4242",
            "exp_month": 10,
            "exp_year": 2028,
        },
        "coupon_code": None,
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["subtotal"] == 165.0
    assert data["tax"] == 10.31
    assert data["total"] == 175.31
    emit_incident.assert_not_called()


def test_regression_inc_7e8a6dfb_california_checkout(monkeypatch):
    """The incident request completes with the California tax rate."""
    emit_incident = Mock(return_value=SimpleNamespace(
        incident_id="inc-7e8a6dfb",
        error_type="TypeError",
        error_message="'builtin_function_or_method' object is not subscriptable",
    ))
    monkeypatch.setattr("app.checkout.emit_incident", emit_incident)
    payload = {
        "cart_items": [
            {"id": "item-101", "name": "Cyberpunk Mechanical Keyboard", "price": 120.0, "quantity": 1},
            {"id": "item-102", "name": "Precision Wireless Mouse", "price": 45.0, "quantity": 1},
        ],
        "shipping_address": {
            "street": "742 Evergreen Terrace",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94103",
            "country": "US",
        },
        "payment_details": {
            "card_number_masked": "•••• •••• •••• 4242",
            "exp_month": 10,
            "exp_year": 2028,
        },
        "coupon_code": None,
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["subtotal"] == 165.0
    assert data["tax"] == 13.61
    assert data["total"] == 178.61
    emit_incident.assert_not_called()


def test_regression_inc_dc3a3a72_florida_checkout(monkeypatch):
    """The incident request completes without subscripting dict.get."""
    emit_incident = Mock(return_value=SimpleNamespace(
        incident_id="inc-dc3a3a72",
        error_type="TypeError",
        error_message="'builtin_function_or_method' object is not subscriptable",
    ))
    monkeypatch.setattr("app.checkout.emit_incident", emit_incident)
    payload = {
        "cart_items": [
            {"id": "item-101", "name": "Cyberpunk Mechanical Keyboard", "price": 120.0, "quantity": 1},
            {"id": "item-102", "name": "Precision Wireless Mouse", "price": 45.0, "quantity": 1},
        ],
        "shipping_address": {
            "street": "742 Evergreen Terrace",
            "city": "San Francisco",
            "state": "FL",
            "postal_code": "94103",
            "country": "US",
        },
        "payment_details": {
            "card_number_masked": "•••• •••• •••• 4242",
            "exp_month": 10,
            "exp_year": 2028,
        },
        "coupon_code": None,
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["subtotal"] == 165.0
    assert data["tax"] == 10.31
    assert data["total"] == 175.31
    emit_incident.assert_not_called()


def test_regression_inc_84f99a6e_florida_checkout(monkeypatch):
    """The exact incident request completes using the default US tax rate."""
    emit_incident = Mock(return_value=SimpleNamespace(
        incident_id="inc-84f99a6e",
        error_type="TypeError",
        error_message="unsupported operand type(s) for *: 'float' and 'NoneType'",
    ))
    monkeypatch.setattr("app.checkout.emit_incident", emit_incident)
    payload = {
        "cart_items": [
            {"id": "item-101", "name": "Cyberpunk Mechanical Keyboard", "price": 120.0, "quantity": 1},
            {"id": "item-102", "name": "Precision Wireless Mouse", "price": 45.0, "quantity": 1},
        ],
        "shipping_address": {
            "street": "742 Evergreen Terrace",
            "city": "San Francisco",
            "state": "FL",
            "postal_code": "94103",
            "country": "US",
        },
        "payment_details": {
            "card_number_masked": "•••• •••• •••• 4242",
            "exp_month": 10,
            "exp_year": 2028,
        },
        "coupon_code": None,
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["subtotal"] == 165.0
    assert data["tax"] == 10.31
    assert data["total"] == 175.31
    emit_incident.assert_not_called()


@pytest.mark.parametrize("country", ["ZZ", " zz "])
def test_tax_with_unlisted_country(country):
    assert calculate_tax(100.0, country=country) == 5.0


def test_regression_inc_18f58562_florida_checkout(monkeypatch):
    """The incident payload uses the US fallback without multiplying by None."""
    emit_incident = Mock(return_value=SimpleNamespace(
        incident_id="inc-18f58562",
        error_type="TypeError",
        error_message="unsupported operand type(s) for *: 'float' and 'NoneType'",
    ))
    monkeypatch.setattr("app.checkout.emit_incident", emit_incident)
    payload = {
        "cart_items": [
            {"id": "item-101", "name": "Cyberpunk Mechanical Keyboard", "price": 120.0, "quantity": 1},
            {"id": "item-102", "name": "Precision Wireless Mouse", "price": 45.0, "quantity": 1},
        ],
        "shipping_address": {
            "street": "742 Evergreen Terrace",
            "city": "San Francisco",
            "state": "FL",
            "postal_code": "94103",
            "country": "US",
        },
        "payment_details": {
            "card_number_masked": "\u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022 4242",
            "exp_month": 10,
            "exp_year": 2028,
        },
        "coupon_code": None,
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["subtotal"] == 165.0
    assert data["tax"] == 10.31
    assert data["total"] == 175.31
    emit_incident.assert_not_called()


@pytest.mark.parametrize("country", [None, ""])
def test_tax_with_missing_country_and_state(country):
    assert calculate_tax(100.0, country=country) == 6.25


def test_tax_with_default_jurisdiction():
    assert calculate_tax(100.0) == 6.25


def test_regression_inc_daa77a88_california_checkout(monkeypatch):
    """The exact incident payload must complete without an undefined tax_rate."""
    emit_incident = Mock(return_value=SimpleNamespace(
        incident_id="inc-daa77a88",
        error_type="NameError",
        error_message="name 'tax_rate' is not defined",
    ))
    monkeypatch.setattr("app.checkout.emit_incident", emit_incident)
    payload = {
        "cart_items": [
            {"id": "item-101", "name": "Cyberpunk Mechanical Keyboard", "price": 120.0, "quantity": 1},
            {"id": "item-102", "name": "Precision Wireless Mouse", "price": 45.0, "quantity": 1},
        ],
        "shipping_address": {
            "street": "742 Evergreen Terrace",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94103",
            "country": "US",
        },
        "payment_details": {
            "card_number_masked": "\u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022 4242",
            "exp_month": 10,
            "exp_year": 2028,
        },
        "coupon_code": None,
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["subtotal"] == 165.0
    assert data["tax"] == 13.61
    assert data["total"] == 178.61
    emit_incident.assert_not_called()


@pytest.mark.parametrize("state", ["FL", "ZZ", None, "", "   "])
def test_us_tax_fallback_for_unlisted_or_missing_state(state):
    assert calculate_tax(100.0, country="US", state=state) == 6.25


def test_us_tax_normalizes_jurisdiction():
    assert calculate_tax(100.0, country=" us ", state=" ca ") == 8.25


def test_health_check():
    """Verify health endpoint responds with healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_successful_checkout_california():
    """Verify checkout in California with valid state tax."""
    payload = {
        "cart_items": [
            {"id": "item-1", "name": "Mechanical Keyboard", "price": 100.0, "quantity": 1}
        ],
        "shipping_address": {
            "street": "123 Market St",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94103",
            "country": "US",
        },
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["subtotal"] == 100.0
    # CA rate is 0.0825 -> 8.25
    assert data["tax"] == 8.25
    assert data["total"] == 108.25
    assert "ord-" in data["order_id"]


def test_successful_checkout_new_york():
    """Verify checkout in New York."""
    payload = {
        "cart_items": [
            {"id": "item-2", "name": "Wireless Mouse", "price": 50.0, "quantity": 2}
        ],
        "shipping_address": {
            "street": "456 5th Ave",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "US",
        },
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["subtotal"] == 100.0
    # NY rate is 0.0850 -> 8.50
    assert data["tax"] == 8.50
    assert data["total"] == 108.50


def test_empty_cart_validation():
    """Verify empty cart yields 400 Bad Request."""
    payload = {
        "cart_items": [],
        "shipping_address": {
            "street": "123 Main St",
            "city": "Austin",
            "state": "TX",
            "postal_code": "78701",
            "country": "US",
        },
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 400


def test_international_checkout_uk():
    """Verify international VAT rate calculation (20%)."""
    payload = {
        "cart_items": [
            {"id": "item-3", "name": "USB-C Hub", "price": 40.0, "quantity": 1}
        ],
        "shipping_address": {
            "street": "10 Downing St",
            "city": "London",
            "state": None,
            "postal_code": "SW1A 2AA",
            "country": "GB",
        },
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["tax"] == 8.00  # 20% of 40
    assert data["total"] == 48.00


def test_regression_inc_80ba62c4_unlisted_jurisdiction():
    """
    REGRESSION TEST automatically generated by Codex Agent.
    Reproduces Incident inc-80ba62c4:
    Error: KeyError - 'FL'
    Shipping Jurisdiction: country=US, state=FL
    """
    payload = {
        "cart_items": [
            {"id": "reg-item-1", "name": "Healing Test Item", "price": 100.0, "quantity": 1}
        ],
        "shipping_address": {
            "street": "100 Innovation Way",
            "city": "Orlando",
            "state": "FL",
            "postal_code": "32801",
            "country": "US",
        },
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["subtotal"] == 100.0
    # Tax should be computed without throwing KeyError
    assert data["tax"] >= 0.0
    assert data["total"] == round(data["subtotal"] + data["tax"], 2)


def test_regression_inc_5e332662_unlisted_jurisdiction():
    """
    REGRESSION TEST automatically generated by Codex Agent.
    Reproduces Incident inc-5e332662:
    Error: NameError - name 'tax_rate' is not defined
    Shipping Jurisdiction: country=US, state=FL
    """
    payload = {
        "cart_items": [
            {"id": "reg-item-1", "name": "Healing Test Item", "price": 100.0, "quantity": 1}
        ],
        "shipping_address": {
            "street": "100 Innovation Way",
            "city": "Orlando",
            "state": "FL",
            "postal_code": "32801",
            "country": "US",
        },
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["subtotal"] == 100.0
    # Tax should be computed without throwing KeyError or NameError
    assert data["tax"] >= 0.0
    assert data["total"] == round(data["subtotal"] + data["tax"], 2)
