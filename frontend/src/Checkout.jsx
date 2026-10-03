import React, { useState } from 'react';
import { submitCheckout } from './api';

export default function Checkout({ onOrderPlaced, onIncidentTriggered }) {
  const [cart] = useState([
    { id: 'item-101', name: 'Cyberpunk Mechanical Keyboard', price: 120.0, quantity: 1 },
    { id: 'item-102', name: 'Precision Wireless Mouse', price: 45.0, quantity: 1 },
  ]);

  const [shipping, setShipping] = useState({
    street: '742 Evergreen Terrace',
    city: 'San Francisco',
    state: 'CA',
    postal_code: '94103',
    country: 'US',
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errorInfo, setErrorInfo] = useState(null);

  const subtotal = cart.reduce((sum, i) => sum + i.price * i.quantity, 0);


  const handleCheckout = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setResult(null);
    setErrorInfo(null);

    const payload = {
      cart_items: cart,
      shipping_address: shipping,
      payment_details: {
        card_number_masked: '•••• •••• •••• 4242',
        exp_month: 10,
        exp_year: 2028,
      },
    };

    try {
      const order = await submitCheckout(payload);
      setResult(order);
      if (onOrderPlaced) onOrderPlaced(order);
    } catch (err) {
      console.error('Checkout error:', err);
      const detail = err.detail || {
        error: 'Server Error (500)',
        error_type: 'UnknownException',
        error_message: err.message,
      };
      setErrorInfo(detail);
      if (onIncidentTriggered) onIncidentTriggered(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background: '#131b2e', borderRadius: '16px', padding: '24px', border: '1px solid #1e293b', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.5)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
          🛒 Store Checkout
        </h2>
        <span style={{ fontSize: '0.75rem', padding: '4px 10px', background: '#1e293b', borderRadius: '20px', color: '#94a3b8', border: '1px solid #334155' }}>
          2 Items in Cart
        </span>
      </div>

      {/* Cart Summary */}
      <div style={{ background: '#0b0f19', borderRadius: '10px', padding: '14px', marginBottom: '20px', border: '1px solid #1e293b' }}>
        {cart.map((item) => (
          <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #1e293b', fontSize: '0.9rem' }}>
            <span style={{ color: '#cbd5e1' }}>{item.name} × {item.quantity}</span>
            <span style={{ fontWeight: 600, color: '#f1f5f9' }}>${(item.price * item.quantity).toFixed(2)}</span>
          </div>
        ))}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px', fontSize: '0.95rem', fontWeight: 600 }}>
          <span style={{ color: '#94a3b8' }}>Subtotal</span>
          <span style={{ color: '#38bdf8' }}>${subtotal.toFixed(2)}</span>
        </div>
      </div>



      {/* Shipping Address Inputs */}
      <form onSubmit={handleCheckout}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '10px', marginBottom: '10px' }}>
          <div>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Street Address</label>
            <input
              type="text"
              value={shipping.street}
              onChange={(e) => setShipping({ ...shipping, street: e.target.value })}
              style={{ width: '100%', boxSizing: 'border-box', background: '#0b0f19', border: '1px solid #334155', borderRadius: '6px', padding: '8px 12px', color: '#f1f5f9', fontSize: '0.85rem' }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>City</label>
            <input
              type="text"
              value={shipping.city}
              onChange={(e) => setShipping({ ...shipping, city: e.target.value })}
              style={{ width: '100%', boxSizing: 'border-box', background: '#0b0f19', border: '1px solid #334155', borderRadius: '6px', padding: '8px 12px', color: '#f1f5f9', fontSize: '0.85rem' }}
            />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginBottom: '18px' }}>
          <div>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>State</label>
            <input
              type="text"
              value={shipping.state}
              onChange={(e) => setShipping({ ...shipping, state: e.target.value.toUpperCase() })}
              style={{ width: '100%', boxSizing: 'border-box', background: '#0b0f19', border: '1px solid #334155', borderRadius: '6px', padding: '8px 12px', color: '#f1f5f9', fontSize: '0.85rem', fontWeight: 600 }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Postal Code</label>
            <input
              type="text"
              value={shipping.postal_code}
              onChange={(e) => setShipping({ ...shipping, postal_code: e.target.value })}
              style={{ width: '100%', boxSizing: 'border-box', background: '#0b0f19', border: '1px solid #334155', borderRadius: '6px', padding: '8px 12px', color: '#f1f5f9', fontSize: '0.85rem' }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Country</label>
            <input
              type="text"
              value={shipping.country}
              onChange={(e) => setShipping({ ...shipping, country: e.target.value.toUpperCase() })}
              style={{ width: '100%', boxSizing: 'border-box', background: '#0b0f19', border: '1px solid #334155', borderRadius: '6px', padding: '8px 12px', color: '#f1f5f9', fontSize: '0.85rem' }}
            />
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: '14px',
            borderRadius: '10px',
            border: 'none',
            background: loading ? '#475569' : 'linear-gradient(135deg, #2563eb, #3b82f6)',
            color: '#ffffff',
            fontWeight: 700,
            fontSize: '1rem',
            cursor: loading ? 'not-allowed' : 'pointer',
            boxShadow: '0 4px 14px rgba(37, 99, 235, 0.4)',
            transition: 'all 0.2s',
          }}
        >
          {loading ? 'Processing Order...' : '⚡ Buy Now'}
        </button>
      </form>

      {/* Result Cards */}
      {result && (
        <div style={{ marginTop: '20px', padding: '16px', background: '#064e3b', borderRadius: '10px', border: '1px solid #10b981' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6ee7b7', fontWeight: 700, fontSize: '0.95rem' }}>
            <span>✅</span> Order Placed Successfully!
          </div>
          <div style={{ fontSize: '0.85rem', color: '#d1fae5', marginTop: '8px', lineHeight: 1.6 }}>
            <div><strong>Order ID:</strong> {result.order_id}</div>
            <div><strong>Subtotal:</strong> ${result.subtotal.toFixed(2)} | <strong>Tax:</strong> ${result.tax.toFixed(2)}</div>
            <div><strong>Total Paid:</strong> ${result.total.toFixed(2)}</div>
            <div style={{ fontSize: '0.75rem', opacity: 0.8, marginTop: '4px' }}>Version: {result.deployment_version}</div>
          </div>
        </div>
      )}

      {errorInfo && (
        <div style={{ marginTop: '20px', padding: '16px', background: '#450a0a', borderRadius: '10px', border: '1px solid #ef4444' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#fca5a5', fontWeight: 700, fontSize: '0.95rem' }}>
            <span>⚠️ HTTP 500: Production Failure</span>
            <span style={{ fontSize: '0.7rem', padding: '2px 8px', background: '#7f1d1d', borderRadius: '4px' }}>
              {errorInfo.incident_id || 'Incident Emitted'}
            </span>
          </div>
          <div style={{ fontSize: '0.85rem', color: '#fecaca', marginTop: '8px', lineHeight: 1.6 }}>
            <div><strong>Exception:</strong> {errorInfo.error_type} ({errorInfo.error_message})</div>
            <div style={{ fontSize: '0.75rem', color: '#fda4af', marginTop: '6px' }}>
              📡 Structured incident emitted to Agent Orchestrator. Watch the autonomous repair loop on the right!
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
