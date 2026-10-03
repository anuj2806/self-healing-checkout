import React, { useState, useEffect } from 'react';
import Checkout from './Checkout';
import { getIncidents, getHealth } from './api';

export default function App() {
  const [incidents, setIncidents] = useState([]);
  const [healthInfo, setHealthInfo] = useState({ version: 'v1.0.0', status: 'checking' });
  const [activeIncident, setActiveIncident] = useState(null);

  // Poll incidents & health
  const refreshData = async () => {
    try {
      const h = await getHealth();
      setHealthInfo(h);
    } catch {
      setHealthInfo({ version: 'offline', status: 'offline' });
    }

    try {
      const incList = await getIncidents();
      setIncidents(incList);
      if (incList.length > 0 && !activeIncident) {
        setActiveIncident(incList[incList.length - 1]);
      }
    } catch {
      // Backend may be starting up
    }
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 2500);
    return () => clearInterval(interval);
  }, []);

  const handleIncidentTriggered = (detail) => {
    refreshData();
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'RESOLVED':
        return <span style={{ background: '#065f46', color: '#6ee7b7', padding: '3px 8px', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 600 }}>RESOLVED</span>;
      case 'VERIFIED':
        return <span style={{ background: '#1e40af', color: '#93c5fd', padding: '3px 8px', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 600 }}>GATES PASSED</span>;
      case 'FIXING':
      case 'INVESTIGATING':
        return <span style={{ background: '#854d0e', color: '#fde047', padding: '3px 8px', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 600 }}>AI FIXING</span>;
      case 'TRIGGERED':
        return <span style={{ background: '#991b1b', color: '#fca5a5', padding: '3px 8px', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 600 }}>TRIGGERED</span>;
      default:
        return <span style={{ background: '#334155', color: '#cbd5e1', padding: '3px 8px', borderRadius: '4px', fontSize: '0.72rem' }}>{status}</span>;
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#090d16', color: '#f8fafc', padding: '24px 32px' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '18px', marginBottom: '28px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ background: 'linear-gradient(135deg, #38bdf8, #818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Self-Healing Checkout
            </span>
            <span style={{ fontSize: '0.7rem', padding: '2px 8px', background: '#1e293b', borderRadius: '6px', color: '#38bdf8', border: '1px solid #334155', WebkitTextFillColor: 'initial' }}>
              Autonomous Loop
            </span>
          </h1>
          <p style={{ margin: '4px 0 0', fontSize: '0.82rem', color: '#94a3b8' }}>
            AI controls the development loop &bull; Deterministic CI/CD controls production safety
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#131b2e', padding: '6px 14px', borderRadius: '8px', border: '1px solid #1e293b', fontSize: '0.8rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: healthInfo.status === 'healthy' ? '#10b981' : '#ef4444' }}></span>
            <span style={{ color: '#94a3b8' }}>Live Version:</span>
            <strong style={{ color: '#38bdf8' }}>{healthInfo.version}</strong>
          </div>
        </div>
      </header>

      {/* Main Content Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '28px' }}>
        {/* Left Column: Checkout Interface */}
        <div>
          <Checkout onIncidentTriggered={handleIncidentTriggered} />

          {/* Architecture Concept Callout */}
          <div style={{ marginTop: '24px', background: '#0f172a', borderRadius: '12px', padding: '18px', border: '1px solid #1e293b' }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '0.9rem', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '6px' }}>
              💡 System Philosophy
            </h3>
            <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.6 }}>
              The coding agent operates strictly inside an <strong>isolated Git worktree</strong>. The AI has zero authority to deploy: deployment occurs only if our <strong>deterministic test gates</strong> (pytest + regression tests + security checks) pass 100%, triggering the automated CI/CD pipeline.
            </p>
          </div>
        </div>

        {/* Right Column: Autonomous Healing Pipeline Visualizer */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Pipeline Monitor Card */}
          <div style={{ background: '#131b2e', borderRadius: '16px', padding: '22px', border: '1px solid #1e293b' }}>
            <h2 style={{ margin: '0 0 16px', fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
              🔄 Incident-Driven Autonomous Pipeline
            </h2>

            {/* Step Progression Diagram */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                { title: '1. Incident Capture & Webhook Emission', desc: 'Backend catches 500 error & emits structured payload with stack trace and context.' },
                { title: '2. Isolated Worktree Creation', desc: 'Orchestrator provisions isolated git worktree (fix/incident-xxx) off HEAD.' },
                { title: '3. Codex Agent Investigation & Regression Test', desc: 'Agent reads logs, locates fault in tax.py, and creates regression test in pytest.' },
                { title: '4. Resilient Fix Synthesis', desc: 'Agent patches tax calculation with fallback handling for unlisted jurisdictions.' },
                { title: '5. Deterministic Verification Gate', desc: 'Pytest suite runs independently. Agent NEVER trusted to approve deployment.' },
                { title: '6. Git Commit, Merge & CI/CD Pipeline', desc: 'Deterministic gates PASS -> Changes committed & pushed -> CI/CD builds & deploys.' },
                { title: '7. Smoke Check & Incident Resolution', desc: 'Health check verified on v1.0.1 -> Incident resolved in registry.' },
              ].map((step, idx) => {
                const isStepActive = incidents.length > 0;
                return (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      background: '#0b0f19',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      border: '1px solid #1e293b',
                    }}
                  >
                    <div
                      style={{
                        width: '24px',
                        height: '24px',
                        borderRadius: '50%',
                        background: '#1e293b',
                        color: '#38bdf8',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        flexShrink: 0,
                      }}
                    >
                      {idx + 1}
                    </div>
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f1f5f9' }}>{step.title}</div>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>{step.desc}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Emitted Incidents Stream */}
          <div style={{ background: '#131b2e', borderRadius: '16px', padding: '22px', border: '1px solid #1e293b' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
                📡 Live Incident Monitor ({incidents.length})
              </h3>
              <button
                onClick={refreshData}
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#cbd5e1', padding: '4px 10px', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer' }}
              >
                Refresh
              </button>
            </div>

            {incidents.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px', color: '#64748b', fontSize: '0.85rem' }}>
                No incidents detected yet. Submit an order or test unexpected inputs to observe the autonomous repair loop!
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {incidents.slice(-4).reverse().map((inc) => (
                  <div
                    key={inc.incident_id}
                    onClick={() => setActiveIncident(inc)}
                    style={{
                      background: activeIncident?.incident_id === inc.incident_id ? '#1e293b' : '#0b0f19',
                      padding: '12px 14px',
                      borderRadius: '8px',
                      border: activeIncident?.incident_id === inc.incident_id ? '1px solid #38bdf8' : '1px solid #1e293b',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontFamily: 'Fira Code, monospace', fontSize: '0.8rem', color: '#38bdf8', fontWeight: 600 }}>
                        {inc.incident_id}
                      </span>
                      {getStatusBadge(inc.status)}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: '6px' }}>
                      <strong>{inc.error_type}</strong>: {inc.error_message}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '4px' }}>
                      {inc.timestamp} &bull; Endpoint: {inc.endpoint}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
