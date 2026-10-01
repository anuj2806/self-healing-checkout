const API_BASE = '';

export async function submitCheckout(payload) {
  const res = await fetch(`${API_BASE}/api/checkout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const error = new Error(data.detail?.error_message || data.detail?.error || 'Checkout failed');
    error.status = res.status;
    error.detail = data.detail || data;
    throw error;
  }

  return data;
}

export async function getIncidents() {
  const res = await fetch(`${API_BASE}/api/incidents`);
  if (!res.ok) {
    throw new Error('Failed to fetch incidents');
  }
  return res.json();
}

export async function getIncidentById(incidentId) {
  const res = await fetch(`${API_BASE}/api/incidents/${incidentId}`);
  if (!res.ok) {
    throw new Error('Failed to fetch incident');
  }
  return res.json();
}

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error('Health check failed');
  }
  return res.json();
}
