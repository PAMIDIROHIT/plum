'use client';

import { useState, useEffect } from 'react';
import { claimService } from '../../services/claimService';

// ─── Confidence Bar ───────────────────────────────────────────────────────────
function ConfidenceBar({ score }) {
  const pct = Math.round((score ?? 0) * 100);
  const color = score >= 0.85 ? '#4ade80' : score >= 0.70 ? '#facc15' : '#f87171';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{
        flex: 1, height: 8, background: 'rgba(255,255,255,0.1)',
        borderRadius: 4, overflow: 'hidden'
      }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 4, transition: 'width 0.4s ease' }} />
      </div>
      <span style={{ fontSize: '0.8rem', color, fontWeight: 700, minWidth: 36 }}>{pct}%</span>
    </div>
  );
}

// ─── Extraction Panel ─────────────────────────────────────────────────────────
function ExtractionPanel({ data }) {
  if (!data) return null;
  const hasAny = data.doctor_name || data.diagnosis || data.medicines?.length || data.bill_breakdown;
  if (!hasAny) return (
    <div style={{ padding: '8px 0', color: 'var(--text-muted)', fontSize: '0.82rem', fontStyle: 'italic' }}>
      Gemini extraction data not available for this claim (text-mode or pre-fix submission).
    </div>
  );

  return (
    <div style={{ display: 'grid', gap: 8 }}>

      {/* Patient & Doctor row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        {data.doctor_name && (
          <div className="extraction-field">
            <span className="ex-label">🩺 Doctor</span>
            <span className="ex-value">{data.doctor_name}</span>
            {data.doctor_registration_number && (
              <span className="ex-sub">Reg: {data.doctor_registration_number}</span>
            )}
          </div>
        )}
        {data.hospital_or_clinic && (
          <div className="extraction-field">
            <span className="ex-label">🏥 Hospital / Clinic</span>
            <span className="ex-value">{data.hospital_or_clinic}</span>
          </div>
        )}
      </div>

      {/* Diagnosis */}
      {data.diagnosis && (
        <div className="extraction-field">
          <span className="ex-label">🔬 Diagnosis (Gemini OCR)</span>
          <span className="ex-value" style={{ color: 'var(--accent)' }}>{data.diagnosis}</span>
        </div>
      )}

      {/* Medicines */}
      {data.medicines?.length > 0 && (
        <div className="extraction-field">
          <span className="ex-label">💊 Medicines Prescribed</span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
            {data.medicines.map((m, i) => (
              <span key={i} style={{
                background: 'rgba(96,165,250,0.15)', border: '1px solid rgba(96,165,250,0.3)',
                borderRadius: 4, padding: '2px 8px', fontSize: '0.78rem', color: '#93c5fd'
              }}>{m}</span>
            ))}
          </div>
        </div>
      )}

      {/* Tests */}
      {data.tests_prescribed?.length > 0 && (
        <div className="extraction-field">
          <span className="ex-label">🧪 Diagnostic Tests</span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
            {data.tests_prescribed.map((t, i) => (
              <span key={i} style={{
                background: 'rgba(167,139,250,0.15)', border: '1px solid rgba(167,139,250,0.3)',
                borderRadius: 4, padding: '2px 8px', fontSize: '0.78rem', color: '#c4b5fd'
              }}>{t}</span>
            ))}
          </div>
        </div>
      )}

      {/* Bill Breakdown */}
      {data.bill_breakdown && Object.keys(data.bill_breakdown).length > 0 && (
        <div className="extraction-field">
          <span className="ex-label">🧾 Bill Breakdown (AI-extracted)</span>
          <table style={{ width: '100%', fontSize: '0.82rem', borderCollapse: 'collapse', marginTop: 6 }}>
            <tbody>
              {Object.entries(data.bill_breakdown).map(([k, v], i) => (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '3px 0', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                    {k.replace(/_/g, ' ')}
                  </td>
                  <td style={{ textAlign: 'right', color: '#4ade80', fontWeight: 600 }}>₹{v?.toLocaleString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* OCR Confidence */}
      {data.ocr_confidence != null && (
        <div className="extraction-field">
          <span className="ex-label">📡 OCR Confidence</span>
          <ConfidenceBar score={data.ocr_confidence} />
        </div>
      )}

      {/* Fraud flags from extraction */}
      {data.possible_fraud_flags?.length > 0 && (
        <div className="extraction-field" style={{ borderLeft: '2px solid #f87171' }}>
          <span className="ex-label" style={{ color: '#f87171' }}>⚠️ Gemini Fraud Indicators</span>
          <ul style={{ margin: '4px 0 0', paddingLeft: 16, color: '#fca5a5', fontSize: '0.82rem' }}>
            {data.possible_fraud_flags.map((f, i) => <li key={i}>{f}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [claims, setClaims] = useState([]);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('audit');

  const fetchClaims = async () => {
    try {
      setLoading(true);
      const data = await claimService.getClaimsHistory();
      setClaims(data);
    } catch (e) {
      console.error('Failed to load history:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchClaims(); }, []);

  const handleManualDecision = async (decision) => {
    if (!selectedClaim) return;
    try {
      await claimService.reviewClaim(selectedClaim.claim_id, decision, reviewNotes);
      setSelectedClaim(null);
      setReviewNotes('');
      fetchClaims();
    } catch (e) {
      console.error(e);
    }
  };

  const totalClaims = claims.length;
  const approvedClaims = claims.filter(c => c.decision === 'APPROVED' || c.decision === 'PARTIAL').length;
  const rejectedClaims = claims.filter(c => c.decision === 'REJECTED').length;
  const reviewPending = claims.filter(c => c.decision === 'MANUAL_REVIEW').length;
  const totalApprovedAmount = claims.reduce((sum, c) => sum + (c.approved_amount || 0), 0);

  return (
    <div className="dashboard-view">
      {/* ── Metrics Header ── */}
      <div className="stats-panel">
        <div className="stat-card">
          <span className="stat-label">Total Claims</span>
          <span className="stat-value">{totalClaims}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Total Approved</span>
          <span className="stat-value text-success">₹{totalApprovedAmount.toLocaleString('en-IN')}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Approved / Partial</span>
          <span className="stat-value text-accent">{approvedClaims}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Rejected</span>
          <span className="stat-value text-danger">{rejectedClaims}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Manual Review</span>
          <span className="stat-value text-warning">{reviewPending}</span>
        </div>
      </div>

      {/* ── Claims Table ── */}
      <div className="glass-card">
        <div className="card-header flex-header">
          <div>
            <h2 className="gradient-text">Claims Audit Ledger</h2>
            <p className="card-subtitle">Real AI pipeline results — Gemini OCR + DeepSeek R1 adjudication stored in SQLite.</p>
          </div>
          <button className="btn-small" onClick={fetchClaims}>🔄 Refresh</button>
        </div>

        {loading ? (
          <div className="empty-state"><p>Loading claims…</p></div>
        ) : totalClaims === 0 ? (
          <div className="empty-state">
            <p>No claims yet. Submit a claim on the Upload tab to run the AI pipeline.</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="claim-table">
              <thead>
                <tr>
                  <th>Claim ID</th>
                  <th>Patient</th>
                  <th>Diagnosis</th>
                  <th>Date</th>
                  <th>Claimed</th>
                  <th>Approved</th>
                  <th>AI Confidence</th>
                  <th>Decision</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {claims.map((claim) => (
                  <tr key={claim.claim_id} className="claim-row">
                    <td className="claim-id-cell">{claim.claim_id}</td>
                    <td>
                      <div className="member-info">
                        <span className="member-name">{claim.member_name}</span>
                        <span className="member-id-tag">{claim.member_id}</span>
                      </div>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: 160 }}>
                      {claim.extraction_data?.diagnosis || '—'}
                    </td>
                    <td>{claim.treatment_date}</td>
                    <td>₹{(claim.claim_amount || 0).toLocaleString('en-IN')}</td>
                    <td className="text-success fw-bold">₹{(claim.approved_amount || 0).toLocaleString('en-IN')}</td>
                    <td style={{ minWidth: 120 }}>
                      <ConfidenceBar score={claim.confidence_score} />
                    </td>
                    <td>
                      <span className={`status-badge badge-${claim.decision?.toLowerCase()}`}>
                        {claim.decision}
                      </span>
                    </td>
                    <td>
                      <button className="btn-small" onClick={() => { setSelectedClaim(claim); setActiveTab('audit'); }}>
                        🔎 Audit Report
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Audit Modal ── */}
      {selectedClaim && (
        <div className="modal-overlay" onClick={() => setSelectedClaim(null)}>
          <div className="modal-content glass-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 800, width: '95vw' }}>
            <div className="modal-header">
              <h3>Audit Report — {selectedClaim.claim_id}</h3>
              <button className="close-btn" onClick={() => setSelectedClaim(null)}>×</button>
            </div>

            {/* Tab navigation */}
            <div style={{ display: 'flex', gap: 8, padding: '0 0 16px', borderBottom: '1px solid rgba(255,255,255,0.07)', marginBottom: 16 }}>
              {['audit', 'extraction', 'reasoning'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  style={{
                    padding: '6px 16px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600,
                    background: activeTab === tab ? 'var(--accent)' : 'rgba(255,255,255,0.08)',
                    color: activeTab === tab ? '#000' : 'var(--text-secondary)',
                    transition: 'all 0.2s'
                  }}
                >
                  {tab === 'audit' ? '⚖️ Adjudication' : tab === 'extraction' ? '🔍 Gemini Extraction' : '🧠 DeepSeek Reasoning'}
                </button>
              ))}
            </div>

            <div className="modal-body">

              {/* ── TAB: Adjudication ── */}
              {activeTab === 'audit' && (
                <div className="modal-grid">
                  <div className="modal-col">
                    <h4>Member & Treatment</h4>
                    <p><strong>Name:</strong> {selectedClaim.member_name}</p>
                    <p><strong>Member ID:</strong> {selectedClaim.member_id}</p>
                    <p><strong>Date:</strong> {selectedClaim.treatment_date}</p>
                    <p><strong>Hospital:</strong> {selectedClaim.input?.hospital || selectedClaim.extraction_data?.hospital_or_clinic || 'Non-Network'}</p>
                    <p><strong>Claimed:</strong> ₹{(selectedClaim.claim_amount || 0).toLocaleString('en-IN')}</p>

                    <h4 className="mt-4">Final Decision</h4>
                    <div className="verdict-banner">
                      <span className={`status-badge badge-${selectedClaim.decision?.toLowerCase()}`}>{selectedClaim.decision}</span>
                      <span className="verdict-amount">₹{(selectedClaim.approved_amount || 0).toLocaleString('en-IN')} approved</span>
                    </div>

                    <div style={{ marginTop: 12 }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>AI Confidence Score</span>
                      <ConfidenceBar score={selectedClaim.confidence_score} />
                    </div>
                  </div>

                  <div className="modal-col">
                    <h4>Adjudication Audit Log</h4>
                    <ul className="audit-logs">
                      <li><strong>Policy Status:</strong> Active ✅</li>
                      {selectedClaim.rejection_reasons?.length > 0 ? (
                        <li className="text-danger">
                          <strong>Rejection Codes:</strong> {selectedClaim.rejection_reasons.join(', ')} ❌
                        </li>
                      ) : (
                        <li><strong>Eligibility & Waiting Period:</strong> Passed ✅</li>
                      )}
                      {selectedClaim.copay_applied > 0 && (
                        <li><strong>Copay:</strong> ₹{selectedClaim.copay_applied} (10%) deducted</li>
                      )}
                      {selectedClaim.network_discount_applied > 0 && (
                        <li><strong>Network Discount:</strong> ₹{selectedClaim.network_discount_applied} (20%) applied</li>
                      )}
                      {selectedClaim.rejected_items?.length > 0 && (
                        <li className="text-warning">
                          <strong>Excluded Items:</strong>
                          <ul className="sub-list">{selectedClaim.rejected_items.map((item, i) => <li key={i}>{item}</li>)}</ul>
                        </li>
                      )}
                      {selectedClaim.approved_items?.length > 0 && (
                        <li>
                          <strong>Approved Items:</strong>
                          <ul className="sub-list">{selectedClaim.approved_items.map((item, i) => <li key={i}>{item}</li>)}</ul>
                        </li>
                      )}
                      {selectedClaim.flags?.length > 0 && (
                        <li className="text-warning">
                          <strong>Fraud Flags:</strong> {selectedClaim.flags.join(', ')} ⚠️
                        </li>
                      )}
                    </ul>
                    <p className="mt-2"><strong>Notes:</strong> {selectedClaim.notes}</p>
                    <p><strong>Next Steps:</strong> {selectedClaim.next_steps}</p>

                    {selectedClaim.policy_violations?.length > 0 && (
                      <div className="mt-4 text-danger">
                        <strong>Policy Violations:</strong>
                        <ul className="sub-list">{selectedClaim.policy_violations.map((v, i) => <li key={i}>{v}</li>)}</ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ── TAB: Gemini Extraction ── */}
              {activeTab === 'extraction' && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                    <span style={{
                      background: 'linear-gradient(135deg, #4285F4, #34A853)',
                      borderRadius: 8, padding: '4px 12px', fontSize: '0.78rem', fontWeight: 700, color: '#fff'
                    }}>
                      ✦ Gemini 2.5 Flash Vision
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Real OCR output from uploaded documents
                    </span>
                  </div>
                  <ExtractionPanel data={selectedClaim.extraction_data} />
                </div>
              )}

              {/* ── TAB: DeepSeek Reasoning ── */}
              {activeTab === 'reasoning' && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                    <span style={{
                      background: 'linear-gradient(135deg, #7c3aed, #3b82f6)',
                      borderRadius: 8, padding: '4px 12px', fontSize: '0.78rem', fontWeight: 700, color: '#fff'
                    }}>
                      🧠 DeepSeek R1 Chain-of-Thought
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      AI adjudication reasoning trace
                    </span>
                  </div>

                  {selectedClaim.reasoning?.length > 0 ? (
                    <ol style={{ paddingLeft: 20, lineHeight: 1.7 }}>
                      {selectedClaim.reasoning.map((r, i) => (
                        <li key={i} style={{ marginBottom: 8, fontSize: '0.88rem', color: 'var(--text-secondary)' }}>{r}</li>
                      ))}
                    </ol>
                  ) : (
                    <div style={{ padding: '12px', background: 'rgba(255,255,255,0.04)', borderRadius: 8, fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      DeepSeek reasoning not available for this claim. This typically means the claim was processed
                      before the model fix (DeepSeek free tier was offline) or the local rules engine handled it.
                      Resubmit the claim to get full AI reasoning.
                    </div>
                  )}

                  {selectedClaim.medical_necessity_analysis?.length > 0 && (
                    <div style={{ marginTop: 20 }}>
                      <strong style={{ color: 'var(--text-primary)', fontSize: '0.88rem' }}>Medical Necessity Analysis:</strong>
                      <ul style={{ paddingLeft: 20, marginTop: 8, lineHeight: 1.7 }}>
                        {selectedClaim.medical_necessity_analysis.map((a, i) => (
                          <li key={i} style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 4 }}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* ── Manual Review Panel ── */}
              {selectedClaim.decision === 'MANUAL_REVIEW' && (
                <div className="manual-review-panel" style={{ marginTop: 20 }}>
                  <h4>✍️ Manual Review Desk</h4>
                  <p className="panel-subtitle">This claim was flagged for human verification. Review AI reasoning above and enter your decision.</p>
                  <textarea
                    rows={3}
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    placeholder="Enter review observations or comments…"
                  />
                  <div className="manual-actions mt-2">
                    <button className="btn-primary" onClick={() => handleManualDecision('APPROVED')}>✅ Approve Claim</button>
                    <button className="btn-secondary" onClick={() => handleManualDecision('REJECTED')}>❌ Reject Claim</button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Extraction field CSS ── */}
      <style>{`
        .extraction-field {
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.07);
          border-radius: 8px;
          padding: 10px 14px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .ex-label { font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
        .ex-value { font-size: 0.9rem; color: var(--text-primary); font-weight: 500; }
        .ex-sub { font-size: 0.78rem; color: var(--text-muted); font-family: monospace; }
      `}</style>
    </div>
  );
}
