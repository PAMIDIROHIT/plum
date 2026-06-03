'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { claimService } from '../../services/claimService';

const PRESCRIPTION_TEMPLATE_VIRAL = `--------------------------------
Dr. Rahul Sharma, MBBS MD
Reg. No: KA/45678/2015
Apollo Clinic, Bangalore
--------------------------------
Date: 2024-11-01

Patient Name: Rajesh Kumar
Age/Sex: 34/M

Diagnosis:
Viral fever

Rx:
1. Tab. Paracetamol 650mg
   1-0-1 x 5 days
2. Tab. Vitamin C 500mg
   0-1-0 x 10 days

Investigations Advised:
- CBC Test
- Dengue test

Dr. Rahul Sharma`;

const BILL_TEMPLATE_VIRAL = `--------------------------------
Apollo Clinic Invoice
GST: 29AAAAA1111A1Z1
--------------------------------
Patient: Rajesh Kumar
Date: 2024-11-01

PARTICULARS               AMOUNT
--------------------------------
Consultation Fee          ₹ 1000
Diagnostic Tests:
- CBC & Dengue Test       ₹ 500
--------------------------------
TOTAL:                   ₹ 1500`;

const PRESCRIPTION_TEMPLATE_DENTAL = `--------------------------------
Dr. Neha Patel, MDS (Dentist)
Reg. No: MH/23456/2018
Patel Dental Care, Mumbai
--------------------------------
Date: 2024-10-15

Patient Name: Priya Singh
Age/Sex: 28/F

Diagnosis:
Tooth decay requiring root canal and aesthetic enhancement

Rx:
- Root canal treatment
- Teeth whitening

Dr. Neha Patel`;

const BILL_TEMPLATE_DENTAL = `--------------------------------
Patel Dental Care Bill
--------------------------------
Patient: Priya Singh
Date: 2024-10-15

PARTICULARS               AMOUNT
--------------------------------
Root Canal Treatment      ₹ 8000
Teeth Whitening           ₹ 4000
--------------------------------
TOTAL:                   ₹ 12000`;

export default function UploadPage() {
  const router = useRouter();

  // Form parameters
  const [memberId, setMemberId] = useState('EMP101');
  const [memberName, setMemberName] = useState('John Doe');
  const [memberJoinDate, setMemberJoinDate] = useState('2024-01-01');
  const [treatmentDate, setTreatmentDate] = useState(new Date().toISOString().split('T')[0]);
  const [claimAmount, setClaimAmount] = useState(1500);
  const [hospital, setHospital] = useState('');
  const [cashlessRequest, setCashlessRequest] = useState(false);
  const [prevClaimsToday, setPrevClaimsToday] = useState(0);

  // Document Raw texts
  const [prescriptionText, setPrescriptionText] = useState(PRESCRIPTION_TEMPLATE_VIRAL);
  const [billText, setBillText] = useState(BILL_TEMPLATE_VIRAL);

  // Status flags
  const [extracting, setExtracting] = useState(false);
  const [adjudicating, setAdjudicating] = useState(false);
  const [adjudicationMode, setAdjudicationMode] = useState('ai');
  const [openrouterKey, setOpenrouterKey] = useState('');

  // Pre-load preset options
  const handleLoadTemplate = (type) => {
    if (type === 'viral') {
      setMemberName('Rajesh Kumar');
      setMemberId('EMP001');
      setTreatmentDate('2024-11-01');
      setClaimAmount(1500);
      setPrescriptionText(PRESCRIPTION_TEMPLATE_VIRAL);
      setBillText(BILL_TEMPLATE_VIRAL);
    } else {
      setMemberName('Priya Singh');
      setMemberId('EMP002');
      setTreatmentDate('2024-10-15');
      setClaimAmount(12000);
      setPrescriptionText(PRESCRIPTION_TEMPLATE_DENTAL);
      setBillText(BILL_TEMPLATE_DENTAL);
    }
  };

  // Submit claim workflow to backend
  const handleSubmit = async () => {
    setAdjudicating(true);
    try {
      const claimPayload = {
        member_id: memberId,
        member_name: memberName,
        member_join_date: memberJoinDate,
        treatment_date: treatmentDate,
        claim_amount: claimAmount,
        hospital: hospital || null,
        cashless_request: cashlessRequest,
        previous_claims_same_day: prevClaimsToday,
        prescription_text: prescriptionText,
        bill_text: billText,
        adjudication_mode: adjudicationMode
      };
      
      // Override backend API key locally if entered
      if (openrouterKey) {
        localStorage.setItem('plum_openrouter_key', openrouterKey);
      }

      await claimService.submitClaim(claimPayload);
      router.push('/dashboard'); // Route back to claims overview
    } catch (e) {
      console.error(e);
      alert('Claims adjudication failed: ' + e.message);
    } finally {
      setAdjudicating(false);
    }
  };

  return (
    <div className="claim-submitter glass-card">
      <div className="card-header">
        <h2 className="gradient-text">Submit Insurance Claim</h2>
        <p className="card-subtitle">Upload digital documents and run the FastAPI + OpenRouter AI rules engine.</p>
      </div>

      <div className="template-row">
        <span>Load Mock Templates:</span>
        <button className="btn-small" onClick={() => handleLoadTemplate('viral')}>🌡️ Viral Fever (TC001)</button>
        <button className="btn-small" onClick={() => handleLoadTemplate('dental')}>🦷 Dental Procedure (TC002)</button>
      </div>

      <div className="adjudicator-form-grid">
        <div className="form-column">
          <h3>👤 Patient & Provider Details</h3>
          
          <div className="input-group">
            <label>Member ID</label>
            <input type="text" value={memberId} onChange={(e) => setMemberId(e.target.value)} />
          </div>

          <div className="input-group">
            <label>Patient Name</label>
            <input type="text" value={memberName} onChange={(e) => setMemberName(e.target.value)} />
          </div>

          <div className="dual-inputs">
            <div className="input-group">
              <label>Join Date</label>
              <input type="date" value={memberJoinDate} onChange={(e) => setMemberJoinDate(e.target.value)} />
            </div>
            <div className="input-group">
              <label>Treatment Date</label>
              <input type="date" value={treatmentDate} onChange={(e) => setTreatmentDate(e.target.value)} />
            </div>
          </div>

          <div className="input-group">
            <label>Claim Amount (₹)</label>
            <input type="number" value={claimAmount} onChange={(e) => setClaimAmount(parseInt(e.target.value, 10))} />
          </div>

          <div className="input-group">
            <label>Provider / Hospital</label>
            <select value={hospital} onChange={(e) => setHospital(e.target.value)}>
              <option value="">Non-Network / Private Clinic</option>
              <option value="Apollo Hospitals">Apollo Hospitals</option>
              <option value="Fortis Healthcare">Fortis Healthcare</option>
              <option value="Max Healthcare">Max Healthcare</option>
              <option value="Manipal Hospitals">Manipal Hospitals</option>
              <option value="Narayana Health">Narayana Health</option>
            </select>
          </div>

          <div className="toggle-group">
            <label className="switch">
              <input type="checkbox" checked={cashlessRequest} onChange={(e) => setCashlessRequest(e.target.checked)} />
              <span className="slider round"></span>
            </label>
            <span>Request Cashless Adjudication</span>
          </div>

          <div className="input-group">
            <label>Claims Submitted Today</label>
            <input type="number" value={prevClaimsToday} onChange={(e) => setPrevClaimsToday(parseInt(e.target.value, 10))} />
          </div>
        </div>

        <div className="form-column">
          <h3>📄 Documents & Model Configuration</h3>

          <div className="input-group">
            <label>Doctor's Prescription (Text)</label>
            <textarea 
              rows={6} 
              value={prescriptionText} 
              onChange={(e) => setPrescriptionText(e.target.value)}
              placeholder="Paste doctor prescription here..."
            />
          </div>

          <div className="input-group">
            <label>Invoice / Invoice Bill (Text)</label>
            <textarea 
              rows={5} 
              value={billText} 
              onChange={(e) => setBillText(e.target.value)}
              placeholder="Paste invoice items and costs here..."
            />
          </div>

          <div className="input-group">
            <label>Adjudication Mode</label>
            <select value={adjudicationMode} onChange={(e) => setAdjudicationMode(e.target.value)}>
              <option value="ai">🧠 Dual LLM Chain (Gemini 2.5 Flash + DeepSeek R1)</option>
              <option value="local">⚡ Local Rules Engine (Instance Verification)</option>
            </select>
          </div>

          <div className="adjudication-actions" style={{ gridTemplateColumns: '1fr' }}>
            <button 
              className="btn-primary" 
              onClick={handleSubmit}
              disabled={adjudicating}
            >
              {adjudicating ? 'Processing Adjudication...' : '⚖️ Submit Claim for Adjudication'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
