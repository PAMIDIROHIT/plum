'use client';

import { useState, useEffect } from 'react';
import { claimService } from '../../services/claimService';

export default function DashboardPage() {
  const [claims, setClaims] = useState([]);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [loading, setLoading] = useState(true);

  // Fetch claims log from FastAPI backend
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

  useEffect(() => {
    fetchClaims();
  }, []);

  // Submit supervisor review updates
  const handleManualDecision = async (decision) => {
    if (!selectedClaim) return;
    try {
      await claimService.reviewClaim(selectedClaim.claim_id, decision, reviewNotes);
      setSelectedClaim(null);
      setReviewNotes('');
      fetchClaims(); // Refresh metrics
    } catch (e) {
      console.error(e);
    }
  };

  // Metrics aggregators
  const totalClaims = claims.length;
  const approvedClaims = claims.filter(c => c.decision === 'APPROVED' || c.decision === 'PARTIAL').length;
  const rejectedClaims = claims.filter(c => c.decision === 'REJECTED').length;
  const reviewPending = claims.filter(c => c.decision === 'MANUAL_REVIEW').length;
  const totalApprovedAmount = claims.reduce((sum, c) => sum + c.approved_amount, 0);

  return (
    <div className="dashboard-view">
      {/* Metrics Header */}
      <div className="stats-panel">
        <div className="stat-card">
          <span className="stat-label">Total Claims Submitted</span>
          <span className="stat-value">{totalClaims}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Total Approved Amount</span>
          <span className="stat-value text-success">₹{totalApprovedAmount}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Claims Approved / Partial</span>
          <span className="stat-value text-accent">{approvedClaims}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Claims Rejected</span>
          <span className="stat-value text-danger">{rejectedClaims}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Pending Manual Review</span>
          <span className="stat-value text-warning">{reviewPending}</span>
        </div>
      </div>

      <div className="glass-card">
        <div className="card-header flex-header">
          <div>
            <h2 className="gradient-text">Processed Claims Audit Ledger</h2>
            <p className="card-subtitle">List of claims, status, and AI confidence parameters retrieved from backend SQLite.</p>
          </div>
          <button className="btn-small" onClick={fetchClaims}>🔄 Refresh Data</button>
        </div>

        {loading ? (
          <div className="empty-state">
            <p>Loading claims ledger...</p>
          </div>
        ) : totalClaims === 0 ? (
          <div className="empty-state">
            <p>No claims logs found. Go to the "Submit Claim" tab to run evaluations!</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="claim-table">
              <thead>
                <tr>
                  <th>Claim ID</th>
                  <th>Patient Name</th>
                  <th>Treatment Date</th>
                  <th>Claimed</th>
                  <th>Approved</th>
                  <th>Confidence</th>
                  <th>Verdict Status</th>
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
                    <td>{claim.treatment_date}</td>
                    <td>₹{claim.claim_amount}</td>
                    <td className="text-success fw-bold">₹{claim.approved_amount}</td>
                    <td>
                      <div className="confidence-meter-container">
                        <div 
                          className="confidence-fill" 
                          style={{ 
                            width: `${claim.confidence_score * 100}%`,
                            backgroundColor: claim.confidence_score >= 0.85 ? '#10b981' : claim.confidence_score >= 0.70 ? '#f59e0b' : '#ef4444'
                          }}
                        />
                        <span className="confidence-text">{Math.round(claim.confidence_score * 100)}%</span>
                      </div>
                    </td>
                    <td>
                      <span className={`status-badge badge-${claim.decision.toLowerCase()}`}>
                        {claim.decision}
                      </span>
                    </td>
                    <td>
                      <button className="btn-small" onClick={() => setSelectedClaim(claim)}>
                        🔎 View Audit Report
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Audit Modal */}
      {selectedClaim && (
        <div className="modal-overlay" onClick={() => setSelectedClaim(null)}>
          <div className="modal-content glass-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Adjudication Audit Report - {selectedClaim.claim_id}</h3>
              <button className="close-btn" onClick={() => setSelectedClaim(null)}>×</button>
            </div>

            <div className="modal-body">
              <div className="modal-grid">
                <div className="modal-col">
                  <h4>Member & Treatment Info</h4>
                  <p><strong>Member Name:</strong> {selectedClaim.member_name}</p>
                  <p><strong>Member ID:</strong> {selectedClaim.member_id}</p>
                  <p><strong>Treatment Date:</strong> {selectedClaim.treatment_date}</p>
                  <p><strong>Hospital Provider:</strong> {selectedClaim.input.hospital || 'Non-Network Provider'}</p>
                  
                  <h4 className="mt-4">Final Verdict</h4>
                  <div className="verdict-banner">
                    <span className={`status-badge badge-${selectedClaim.decision.toLowerCase()}`}>
                      {selectedClaim.decision}
                    </span>
                    <span className="verdict-amount">₹{selectedClaim.approved_amount} approved</span>
                  </div>
                </div>

                <div className="modal-col">
                  <h4>Adjudication Audit Logs</h4>
                  <ul className="audit-logs">
                    <li>
                      <strong>Basic Policy Status Check:</strong> Active ✅
                    </li>
                    {selectedClaim.rejection_reasons.length > 0 ? (
                      <li className="text-danger">
                        <strong>Hard Rejections Triggered:</strong> {selectedClaim.rejection_reasons.join(', ')} ❌
                      </li>
                    ) : (
                      <li>
                        <strong>Initial Eligibility & Waiting Period Check:</strong> Passed ✅
                      </li>
                    )}
                    {selectedClaim.copay_applied !== undefined && (
                      <li>
                        <strong>Copay Adjustment:</strong> Deducted ₹{selectedClaim.copay_applied} (10% Copay applied)
                      </li>
                    )}
                    {selectedClaim.network_discount_applied !== undefined && (
                      <li>
                        <strong>Network Discount Applied:</strong> Saved ₹{selectedClaim.network_discount_applied} (20% network discount)
                      </li>
                    )}
                    {selectedClaim.rejected_items && selectedClaim.rejected_items.length > 0 && (
                      <li className="text-warning">
                        <strong>Excluded/Rejected Items:</strong>
                        <ul className="sub-list">
                          {selectedClaim.rejected_items.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </li>
                    )}
                    {selectedClaim.flags && selectedClaim.flags.length > 0 && (
                      <li className="text-warning">
                        <strong>Security & Fraud Flags:</strong> {selectedClaim.flags.join(', ')} ⚠️
                      </li>
                    )}
                  </ul>

                  <p className="mt-2"><strong>Notes:</strong> {selectedClaim.notes}</p>
                  <p><strong>Next Steps:</strong> {selectedClaim.next_steps}</p>

                  {selectedClaim.policy_violations && selectedClaim.policy_violations.length > 0 && (
                    <div className="mt-4 text-danger">
                      <strong>Policy Violations:</strong>
                      <ul className="sub-list">
                        {selectedClaim.policy_violations.map((v, i) => <li key={i}>{v}</li>)}
                      </ul>
                    </div>
                  )}

                  {selectedClaim.medical_necessity_analysis && selectedClaim.medical_necessity_analysis.length > 0 && (
                    <div className="mt-4">
                      <strong>Medical Necessity Review:</strong>
                      <ul className="sub-list" style={{ color: 'var(--text-secondary)' }}>
                        {selectedClaim.medical_necessity_analysis.map((a, i) => <li key={i}>{a}</li>)}
                      </ul>
                    </div>
                  )}

                  {selectedClaim.reasoning && selectedClaim.reasoning.length > 0 && (
                    <div className="mt-4" style={{ fontSize: '0.85rem' }}>
                      <strong>DeepSeek R1 Adjudication Pipeline:</strong>
                      <ul className="sub-list" style={{ color: 'var(--text-muted)' }}>
                        {selectedClaim.reasoning.map((r, i) => <li key={i}>{r}</li>)}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {selectedClaim.decision === 'MANUAL_REVIEW' && (
                <div className="manual-review-panel">
                  <h4>✍️ Manual Claims Review Desk</h4>
                  <p className="panel-subtitle">This claim was flagged for human verification. Approve or Reject this claim manually below.</p>
                  <textarea 
                    rows={3} 
                    value={reviewNotes} 
                    onChange={(e) => setReviewNotes(e.target.value)} 
                    placeholder="Enter manual review observations or comments..."
                  />
                  <div className="manual-actions mt-2">
                    <button className="btn-primary" onClick={() => handleManualDecision('APPROVED')}>
                      Approve Claim
                    </button>
                    <button className="btn-secondary" onClick={() => handleManualDecision('REJECTED')}>
                      Reject Claim
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
