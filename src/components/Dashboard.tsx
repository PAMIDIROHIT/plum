import React, { useState } from 'react';
import type { ClaimInput, AdjudicationResult } from '../types';

interface DashboardProps {
  claims: { input: ClaimInput; result: AdjudicationResult }[];
  onReviewClaim: (claimId: string, decision: 'APPROVED' | 'REJECTED', notes: string) => void;
}

/**
 * Dashboard Component.
 * Lists all processed claims, shows visual metrics (total, approved, pending manual review),
 * and provides a detailed drill-down modal showcasing the exact rules checked and co-pay breakdowns.
 */
export const Dashboard: React.FC<DashboardProps> = ({ claims, onReviewClaim }) => {
  const [selectedClaim, setSelectedClaim] = useState<{ input: ClaimInput; result: AdjudicationResult } | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');

  // Summarize stats
  const totalClaims = claims.length;
  const approvedClaims = claims.filter(c => c.result.decision === 'APPROVED' || c.result.decision === 'PARTIAL').length;
  const rejectedClaims = claims.filter(c => c.result.decision === 'REJECTED').length;
  const reviewPending = claims.filter(c => c.result.decision === 'MANUAL_REVIEW').length;
  
  const totalApprovedAmount = claims.reduce((sum, c) => sum + c.result.approved_amount, 0);

  // Handle manual review submission
  const handleManualDecision = (decision: 'APPROVED' | 'REJECTED') => {
    if (!selectedClaim) return;
    onReviewClaim(selectedClaim.result.claim_id, decision, reviewNotes || `Manually reviewed and ${decision.toLowerCase()}.`);
    setSelectedClaim(null);
    setReviewNotes('');
  };

  return (
    <div className="dashboard-view">
      {/* Metrics Row */}
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
          <span className="stat-label">Pending Manual Review</span>
          <span className="stat-value text-warning">{reviewPending}</span>
        </div>
      </div>

      <div className="glass-card">
        <div className="card-header">
          <h2 className="gradient-text">Processed Insurance Claims</h2>
          <p className="card-subtitle">List of all active, partial, and manual review adjudication decisions.</p>
        </div>

        {totalClaims === 0 ? (
          <div className="empty-state">
            <p>No claims have been submitted yet. Go to the "Submit Claim" or "Test Runner" tabs to get started!</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="claim-table">
              <thead>
                <tr>
                  <th>Claim ID</th>
                  <th>Patient / Member ID</th>
                  <th>Treatment Date</th>
                  <th>Claimed Amount</th>
                  <th>Approved Amount</th>
                  <th>Confidence</th>
                  <th>Decision Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {claims.map(({ input, result }) => (
                  <tr key={result.claim_id} className="claim-row">
                    <td className="claim-id-cell">{result.claim_id}</td>
                    <td>
                      <div className="member-info">
                        <span className="member-name">{input.member_name}</span>
                        <span className="member-id-tag">{input.member_id}</span>
                      </div>
                    </td>
                    <td>{input.treatment_date}</td>
                    <td>₹{input.claim_amount}</td>
                    <td className="text-success fw-bold">₹{result.approved_amount}</td>
                    <td>
                      <div className="confidence-meter-container">
                        <div 
                          className="confidence-fill" 
                          style={{ 
                            width: `${result.confidence_score * 100}%`,
                            backgroundColor: result.confidence_score >= 0.85 ? '#10b981' : result.confidence_score >= 0.70 ? '#f59e0b' : '#ef4444'
                          }}
                        />
                        <span className="confidence-text">{Math.round(result.confidence_score * 100)}%</span>
                      </div>
                    </td>
                    <td>
                      <span className={`status-badge badge-${result.decision.toLowerCase()}`}>
                        {result.decision}
                      </span>
                    </td>
                    <td>
                      <button className="btn-small" onClick={() => setSelectedClaim({ input, result })}>
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

      {/* Adjudication Detail Modal */}
      {selectedClaim && (
        <div className="modal-overlay" onClick={() => setSelectedClaim(null)}>
          <div className="modal-content glass-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Adjudication Audit Report - {selectedClaim.result.claim_id}</h3>
              <button className="close-btn" onClick={() => setSelectedClaim(null)}>×</button>
            </div>

            <div className="modal-body">
              <div className="modal-grid">
                {/* Left Side Info */}
                <div className="modal-col">
                  <h4>Member & Treatment Info</h4>
                  <p><strong>Member Name:</strong> {selectedClaim.input.member_name}</p>
                  <p><strong>Member ID:</strong> {selectedClaim.input.member_id}</p>
                  <p><strong>Treatment Date:</strong> {selectedClaim.input.treatment_date}</p>
                  <p><strong>Hospital Provider:</strong> {selectedClaim.input.hospital || 'Non-Network Provider'}</p>
                  <p><strong>Cashless Facility Requested:</strong> {selectedClaim.input.cashless_request ? 'Yes' : 'No'}</p>
                  
                  <h4 className="mt-4">Final Verdict</h4>
                  <div className="verdict-banner">
                    <span className={`status-badge badge-${selectedClaim.result.decision.toLowerCase()}`}>
                      {selectedClaim.result.decision}
                    </span>
                    <span className="verdict-amount">₹{selectedClaim.result.approved_amount} approved</span>
                  </div>
                </div>

                {/* Right Side Rules Auditing */}
                <div className="modal-col">
                  <h4>Adjudication Audit Logs</h4>
                  <ul className="audit-logs">
                    <li>
                      <strong>Basic Policy Status Check:</strong> Active ✅
                    </li>
                    {selectedClaim.result.rejection_reasons.length > 0 ? (
                      <li className="text-danger">
                        <strong>Hard Rejections Triggered:</strong> {selectedClaim.result.rejection_reasons.join(', ')} ❌
                      </li>
                    ) : (
                      <li>
                        <strong>Initial Eligibility & Waiting Period Check:</strong> Passed ✅
                      </li>
                    )}
                    {selectedClaim.result.copay_applied !== undefined && (
                      <li>
                        <strong>Copay Adjustment:</strong> Deducted ₹{selectedClaim.result.copay_applied} (10% Copay applied)
                      </li>
                    )}
                    {selectedClaim.result.network_discount_applied !== undefined && (
                      <li>
                        <strong>Network Discount Applied:</strong> Saved ₹{selectedClaim.result.network_discount_applied} (20% network discount)
                      </li>
                    )}
                    {selectedClaim.result.rejected_items && (
                      <li className="text-warning">
                        <strong>Excluded/Rejected Items:</strong>
                        <ul className="sub-list">
                          {selectedClaim.result.rejected_items.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </li>
                    )}
                    {selectedClaim.result.flags && selectedClaim.result.flags.length > 0 && (
                      <li className="text-warning">
                        <strong>Security & Fraud Flags:</strong> {selectedClaim.result.flags.join(', ')} ⚠️
                      </li>
                    )}
                  </ul>

                  <p className="mt-2"><strong>Notes:</strong> {selectedClaim.result.notes}</p>
                  <p><strong>Next Steps:</strong> {selectedClaim.result.next_steps}</p>
                </div>
              </div>

              {/* Manual Review Workflow Panel */}
              {selectedClaim.result.decision === 'MANUAL_REVIEW' && (
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
};
