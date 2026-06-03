'use client';

import { useState, useEffect } from 'react';
import { claimService } from '../../services/claimService';

/**
 * Policy Console Page component.
 * Allows claims administrators to dynamically view and update insurance coverage limits,
 * waiting periods, and exclusions.
 */
export default function PolicyConfigPage() {
  const [policy, setPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  // Fetch active policy configuration
  const fetchPolicy = async () => {
    try {
      setLoading(true);
      const data = await claimService.getPolicy();
      setPolicy(data);
    } catch (e) {
      console.error('Failed to load policy:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicy();
  }, []);

  // Handle nested parameter updates
  const handleNestedChange = (category, field, value) => {
    setPolicy((prev) => ({
      ...prev,
      coverage_details: {
        ...prev.coverage_details,
        [category]: {
          ...prev.coverage_details[category],
          [field]: value,
        },
      },
    }));
  };

  // Submit policy updates to backend SQLite/JSON file
  const handleSavePolicy = async () => {
    setSaving(true);
    setSuccessMsg('');
    try {
      await claimService.updatePolicy(policy);
      setSuccessMsg('Policy configuration saved successfully! ✅');
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (e) {
      console.error(e);
      alert('Failed to save policy: ' + e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="glass-card empty-state">
        <p>Loading policy configuration console...</p>
      </div>
    );
  }

  if (!policy) {
    return (
      <div className="glass-card empty-state">
        <p className="text-danger">Failed to load policy config. Ensure backend is running.</p>
      </div>
    );
  }

  return (
    <div className="policy-config-view glass-card">
      <div className="card-header flex-header">
        <div>
          <h2 className="gradient-text">Policy Terms Configuration Console</h2>
          <p className="card-subtitle">
            Configure rules, sub-limits, co-payments, and waiting periods applied by the rule engine.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {successMsg && <span className="text-success fw-bold">{successMsg}</span>}
          <button className="btn-primary" onClick={handleSavePolicy} disabled={saving}>
            {saving ? 'Saving...' : '💾 Save Configurations'}
          </button>
        </div>
      </div>

      <div className="adjudicator-form-grid" style={{ marginTop: '24px' }}>
        <div className="form-column">
          <h3>📈 Global Coverage Sub-limits</h3>
          
          <div className="input-group">
            <label>Policy Code / Name</label>
            <input 
              type="text" 
              value={policy.policy_name} 
              onChange={(e) => setPolicy({...policy, policy_name: e.target.value})} 
            />
          </div>

          <div className="dual-inputs">
            <div className="input-group">
              <label>Annual Policy Limit (₹)</label>
              <input 
                type="number" 
                value={policy.coverage_details.annual_limit} 
                onChange={(e) => setPolicy({
                  ...policy,
                  coverage_details: { ...policy.coverage_details, annual_limit: parseInt(e.target.value, 10) }
                })} 
              />
            </div>
            <div className="input-group">
              <label>Per-Claim Max Limit (₹)</label>
              <input 
                type="number" 
                value={policy.coverage_details.per_claim_limit} 
                onChange={(e) => setPolicy({
                  ...policy,
                  coverage_details: { ...policy.coverage_details, per_claim_limit: parseInt(e.target.value, 10) }
                })} 
              />
            </div>
          </div>

          <h3 className="mt-4">🩺 Consultations & Diagnostics</h3>
          <div className="dual-inputs">
            <div className="input-group">
              <label>Consultation Co-Pay (%)</label>
              <input 
                type="number" 
                value={policy.coverage_details.consultation_fees.copay_percentage} 
                onChange={(e) => handleNestedChange('consultation_fees', 'copay_percentage', parseInt(e.target.value, 10))} 
              />
            </div>
            <div className="input-group">
              <label>Network Discount (%)</label>
              <input 
                type="number" 
                value={policy.coverage_details.consultation_fees.network_discount} 
                onChange={(e) => handleNestedChange('consultation_fees', 'network_discount', parseInt(e.target.value, 10))} 
              />
            </div>
          </div>

          <div className="input-group">
            <label>Diagnostic Test Sub-Limit (₹)</label>
            <input 
              type="number" 
              value={policy.coverage_details.diagnostic_tests.sub_limit} 
              onChange={(e) => handleNestedChange('diagnostic_tests', 'sub_limit', parseInt(e.target.value, 10))} 
            />
          </div>

          <h3 className="mt-4">💊 Pharmacy & Drugs</h3>
          <div className="toggle-group">
            <label className="switch">
              <input 
                type="checkbox" 
                checked={policy.coverage_details.pharmacy.generic_drugs_mandatory} 
                onChange={(e) => handleNestedChange('pharmacy', 'generic_drugs_mandatory', e.target.checked)} 
              />
              <span className="slider round"></span>
            </label>
            <span>Generic Drugs Mandatory</span>
          </div>

          <div className="input-group">
            <label>Branded Drugs Co-Pay (%)</label>
            <input 
              type="number" 
              value={policy.coverage_details.pharmacy.branded_drugs_copay} 
              onChange={(e) => handleNestedChange('pharmacy', 'branded_drugs_copay', parseInt(e.target.value, 10))} 
            />
          </div>
        </div>

        <div className="form-column">
          <h3>⏳ Waiting Periods (Days)</h3>
          
          <div className="dual-inputs">
            <div className="input-group">
              <label>Initial Waiting Period</label>
              <input 
                type="number" 
                value={policy.waiting_periods.initial_waiting} 
                onChange={(e) => setPolicy({
                  ...policy,
                  waiting_periods: { ...policy.waiting_periods, initial_waiting: parseInt(e.target.value, 10) }
                })} 
              />
            </div>
            <div className="input-group">
              <label>Pre-Existing Diseases</label>
              <input 
                type="number" 
                value={policy.waiting_periods.pre_existing_diseases} 
                onChange={(e) => setPolicy({
                  ...policy,
                  waiting_periods: { ...policy.waiting_periods, pre_existing_diseases: parseInt(e.target.value, 10) }
                })} 
              />
            </div>
          </div>

          <h4 className="mt-4">Specific Ailments Waiting (Days)</h4>
          <div className="dual-inputs">
            <div className="input-group">
              <label>Diabetes Waiting</label>
              <input 
                type="number" 
                value={policy.waiting_periods.specific_ailments.diabetes} 
                onChange={(e) => setPolicy({
                  ...policy,
                  waiting_periods: {
                    ...policy.waiting_periods,
                    specific_ailments: { ...policy.waiting_periods.specific_ailments, diabetes: parseInt(e.target.value, 10) }
                  }
                })} 
              />
            </div>
            <div className="input-group">
              <label>Hypertension Waiting</label>
              <input 
                type="number" 
                value={policy.waiting_periods.specific_ailments.hypertension} 
                onChange={(e) => setPolicy({
                  ...policy,
                  waiting_periods: {
                    ...policy.waiting_periods,
                    specific_ailments: { ...policy.waiting_periods.specific_ailments, hypertension: parseInt(e.target.value, 10) }
                  }
                })} 
              />
            </div>
          </div>

          <h3 className="mt-4">🦷 Dental & Vision Coverage</h3>
          <div className="dual-inputs">
            <div className="input-group">
              <label>Dental Sub-Limit (₹)</label>
              <input 
                type="number" 
                value={policy.coverage_details.dental.sub_limit} 
                onChange={(e) => handleNestedChange('dental', 'sub_limit', parseInt(e.target.value, 10))} 
              />
            </div>
            <div className="input-group">
              <label>Vision Sub-Limit (₹)</label>
              <input 
                type="number" 
                value={policy.coverage_details.vision.sub_limit} 
                onChange={(e) => handleNestedChange('vision', 'sub_limit', parseInt(e.target.value, 10))} 
              />
            </div>
          </div>

          <div className="toggle-group" style={{ marginTop: '16px' }}>
            <label className="switch">
              <input 
                type="checkbox" 
                checked={policy.coverage_details.dental.cosmetic_procedures} 
                onChange={(e) => handleNestedChange('dental', 'cosmetic_procedures', e.target.checked)} 
              />
              <span className="slider round"></span>
            </label>
            <span>Allow Cosmetic Dental Procedures</span>
          </div>
        </div>
      </div>
    </div>
  );
}
