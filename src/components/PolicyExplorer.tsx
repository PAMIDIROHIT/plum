import type { PolicyTerms } from '../types';

interface PolicyExplorerProps {
  policy: PolicyTerms;
  onUpdatePolicy: (updatedPolicy: PolicyTerms) => void;
}

/**
 * PolicyExplorer Component.
 * Renders an interactive interface to view and modify policy limits, exclusions,
 * and waiting periods in real-time. Changes are instantly reflected in the adjudicator.
 */
export const PolicyExplorer: React.FC<PolicyExplorerProps> = ({ policy, onUpdatePolicy }) => {
  // Handler to modify policy numbers (limits, copays)
  const handleLimitChange = (path: string[], value: number) => {
    const updated = JSON.parse(JSON.stringify(policy));
    let current = updated;
    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]];
    }
    current[path[path.length - 1]] = value;
    onUpdatePolicy(updated);
  };

  return (
    <div className="policy-explorer glass-card">
      <div className="card-header">
        <h2 className="gradient-text">Policy & Rules Configurator</h2>
        <p className="card-subtitle">
          View or adjust policy terms dynamically. Modified rules apply instantly to new and re-run claims.
        </p>
      </div>

      <div className="policy-grid">
        {/* Core Limits Column */}
        <div className="policy-section">
          <h3>🏆 Core Coverage Limits</h3>
          <div className="input-group">
            <label>Policy ID</label>
            <input type="text" value={policy.policy_id} disabled className="input-disabled" />
          </div>
          <div className="input-group">
            <label>Annual Policy Limit (₹)</label>
            <input
              type="number"
              value={policy.coverage_details.annual_limit}
              onChange={(e) => handleLimitChange(['coverage_details', 'annual_limit'], parseInt(e.target.value, 10))}
            />
          </div>
          <div className="input-group">
            <label>Single Per-Claim Limit (₹)</label>
            <input
              type="number"
              value={policy.coverage_details.per_claim_limit}
              onChange={(e) => handleLimitChange(['coverage_details', 'per_claim_limit'], parseInt(e.target.value, 10))}
            />
          </div>
          <div className="input-group">
            <label>Family Floater Limit (₹)</label>
            <input
              type="number"
              value={policy.coverage_details.family_floater_limit}
              onChange={(e) => handleLimitChange(['coverage_details', 'family_floater_limit'], parseInt(e.target.value, 10))}
            />
          </div>
        </div>

        {/* Category Sub-Limits Column */}
        <div className="policy-section">
          <h3>🩺 Category Sub-limits & Co-payments</h3>
          
          <div className="sub-limit-row">
            <h4>Consultation Fees</h4>
            <div className="dual-inputs">
              <div className="input-group">
                <label>Limit (₹)</label>
                <input
                  type="number"
                  value={policy.coverage_details.consultation_fees.sub_limit}
                  onChange={(e) => handleLimitChange(['coverage_details', 'consultation_fees', 'sub_limit'], parseInt(e.target.value, 10))}
                />
              </div>
              <div className="input-group">
                <label>Copay (%)</label>
                <input
                  type="number"
                  value={policy.coverage_details.consultation_fees.copay_percentage}
                  onChange={(e) => handleLimitChange(['coverage_details', 'consultation_fees', 'copay_percentage'], parseInt(e.target.value, 10))}
                />
              </div>
            </div>
          </div>

          <div className="sub-limit-row">
            <h4>Pharmacy / Medicines</h4>
            <div className="dual-inputs">
              <div className="input-group">
                <label>Sub-limit (₹)</label>
                <input
                  type="number"
                  value={policy.coverage_details.pharmacy.sub_limit}
                  onChange={(e) => handleLimitChange(['coverage_details', 'pharmacy', 'sub_limit'], parseInt(e.target.value, 10))}
                />
              </div>
              <div className="input-group">
                <label>Branded Copay (%)</label>
                <input
                  type="number"
                  value={policy.coverage_details.pharmacy.branded_drugs_copay}
                  onChange={(e) => handleLimitChange(['coverage_details', 'pharmacy', 'branded_drugs_copay'], parseInt(e.target.value, 10))}
                />
              </div>
            </div>
          </div>

          <div className="sub-limit-row">
            <h4>Dental Coverage</h4>
            <div className="dual-inputs">
              <div className="input-group">
                <label>Sub-limit (₹)</label>
                <input
                  type="number"
                  value={policy.coverage_details.dental.sub_limit}
                  onChange={(e) => handleLimitChange(['coverage_details', 'dental', 'sub_limit'], parseInt(e.target.value, 10))}
                />
              </div>
              <div className="input-group">
                <label>Checkup Cap (₹)</label>
                <input
                  type="number"
                  value={policy.coverage_details.dental.routine_checkup_limit}
                  onChange={(e) => handleLimitChange(['coverage_details', 'dental', 'routine_checkup_limit'], parseInt(e.target.value, 10))}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Waiting Periods Column */}
        <div className="policy-section">
          <h3>⏳ Waiting Periods (Days)</h3>
          <div className="input-group">
            <label>Initial Waiting Period</label>
            <input
              type="number"
              value={policy.waiting_periods.initial_waiting}
              onChange={(e) => handleLimitChange(['waiting_periods', 'initial_waiting'], parseInt(e.target.value, 10))}
            />
          </div>
          <div className="input-group">
            <label>Pre-Existing Diseases (PED)</label>
            <input
              type="number"
              value={policy.waiting_periods.pre_existing_diseases}
              onChange={(e) => handleLimitChange(['waiting_periods', 'pre_existing_diseases'], parseInt(e.target.value, 10))}
            />
          </div>
          <div className="input-group">
            <label>Diabetes Waiting Period</label>
            <input
              type="number"
              value={policy.waiting_periods.specific_ailments.diabetes}
              onChange={(e) => handleLimitChange(['waiting_periods', 'specific_ailments', 'diabetes'], parseInt(e.target.value, 10))}
            />
          </div>
          <div className="input-group">
            <label>Hypertension Waiting Period</label>
            <input
              type="number"
              value={policy.waiting_periods.specific_ailments.hypertension}
              onChange={(e) => handleLimitChange(['waiting_periods', 'specific_ailments', 'hypertension'], parseInt(e.target.value, 10))}
            />
          </div>
        </div>
      </div>

      <hr className="divider" />

      <div className="exclusions-network-view">
        <div className="list-panel">
          <h4>🚫 Policy Exclusions</h4>
          <ul className="badge-list">
            {policy.exclusions.map((exclusion, index) => (
              <li key={index} className="exclusion-badge">{exclusion}</li>
            ))}
          </ul>
        </div>
        <div className="list-panel">
          <h4>🏥 Network Hospitals (20% Discount)</h4>
          <ul className="badge-list">
            {policy.network_hospitals.map((hospital, index) => (
              <li key={index} className="hospital-badge">{hospital}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
