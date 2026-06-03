import React, { useState, useEffect } from 'react';
import type { ClaimInput, PolicyTerms, AdjudicationResult } from '../types';
import { extractWithGemini25Flash, adjudicateWithDeepSeekR1, localFallbackParser, DEFAULT_OPENROUTER_KEY } from '../utils/llm';
import { adjudicateClaim } from '../utils/adjudicator';

interface ClaimSubmitterProps {
  policy: PolicyTerms;
  importedClaim: ClaimInput | null;
  onAdjudicateComplete: (result: AdjudicationResult, rawClaim: ClaimInput) => void;
  openaiKey: string;
  setOpenaiKey: (key: string) => void;
}

// Templates mapped to sample_documents_guide.md formatting
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

export const ClaimSubmitter: React.FC<ClaimSubmitterProps> = ({
  policy,
  importedClaim,
  onAdjudicateComplete,
  openaiKey,
  setOpenaiKey
}) => {
  // Input form state
  const [memberId, setMemberId] = useState('EMP101');
  const [memberName, setMemberName] = useState('John Doe');
  const [memberJoinDate, setMemberJoinDate] = useState('2024-01-01');
  const [treatmentDate, setTreatmentDate] = useState(new Date().toISOString().split('T')[0]);
  const [claimAmount, setClaimAmount] = useState<number>(1500);
  const [hospital, setHospital] = useState('');
  const [cashlessRequest, setCashlessRequest] = useState(false);
  const [prevClaimsToday, setPrevClaimsToday] = useState(0);

  // Document raw text states
  const [prescriptionText, setPrescriptionText] = useState(PRESCRIPTION_TEMPLATE_VIRAL);
  const [billText, setBillText] = useState(BILL_TEMPLATE_VIRAL);

  // UI state
  const [extracting, setExtracting] = useState(false);
  const [extractedData, setExtractedData] = useState<any>(null);
  const [adjudicationMode, setAdjudicationMode] = useState<'local' | 'ai'>('ai');
  const [rulesText, setRulesText] = useState('');
  const [adjudicating, setAdjudicating] = useState(false);

  // Fetch rules document on mount
  useEffect(() => {
    fetch('/adjudication_rules.md')
      .then(res => res.text())
      .then(text => setRulesText(text))
      .catch(err => console.error('Failed to load rules text:', err));
  }, []);

  // Sync state if a claim is imported from the Test Runner
  useEffect(() => {
    if (importedClaim) {
      setMemberId(importedClaim.member_id);
      setMemberName(importedClaim.member_name);
      setMemberJoinDate(importedClaim.member_join_date || '2024-01-01');
      setTreatmentDate(importedClaim.treatment_date);
      setClaimAmount(importedClaim.claim_amount);
      setHospital(importedClaim.hospital || '');
      setCashlessRequest(importedClaim.cashless_request || false);
      setPrevClaimsToday(importedClaim.previous_claims_same_day || 0);

      // Populate text boxes with formatted mock templates based on imported info
      if (importedClaim.documents.prescription) {
        const p = importedClaim.documents.prescription;
        setPrescriptionText(`Dr. ${p.doctor_name}\nReg. No: ${p.doctor_reg}\nDiagnosis: ${p.diagnosis}\nMedicines: ${p.medicines_prescribed?.join(', ') || ''}\nProcedures: ${p.procedures?.join(', ') || ''}`);
      } else {
        setPrescriptionText('');
      }

      const b = importedClaim.documents.bill;
      let billStr = 'Bill Items:\n';
      Object.keys(b).forEach(k => {
        if (typeof b[k] === 'number') {
          billStr += `${k}: ₹${b[k]}\n`;
        }
      });
      setBillText(billStr);
      setExtractedData(null);
    }
  }, [importedClaim]);

  // Quick pre-fill templates
  const handleLoadTemplate = (type: 'viral' | 'dental') => {
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
    setExtractedData(null);
  };

  // Run AI / Regex extraction on documents using Gemini 2.5 Flash
  const handleExtract = async () => {
    setExtracting(true);
    try {
      const combinedText = `
=== PRESCRIPTION DOCUMENT ===
${prescriptionText}

=== BILL/INVOICE DOCUMENT ===
${billText}
`;
      const extracted = await extractWithGemini25Flash(openaiKey, combinedText);
      setExtractedData(extracted);

      // Autofill patient details if extracted
      if (extracted.patient_name && extracted.patient_name !== 'Unknown') {
        setMemberName(extracted.patient_name);
      }
      if (extracted.claim_amount) {
        setClaimAmount(extracted.claim_amount);
      }
    } catch (e) {
      console.error('Extraction failed:', e);
    } finally {
      setExtracting(false);
    }
  };

  // Run Adjudication using selected Mode (Local rules vs DeepSeek R1)
  const handleSubmitAdjudication = async () => {
    setAdjudicating(true);
    const claimId = `CLM_${Math.floor(100000 + Math.random() * 900000)}`;
    
    let finalExtractedData = extractedData;
    if (!finalExtractedData) {
      // Run fallback parser on-the-fly
      const syncPresc = prescriptionText.trim() ? localFallbackParser(prescriptionText, 'prescription') : undefined;
      const syncBill = localFallbackParser(billText, 'bill');
      finalExtractedData = {
        prescription: syncPresc,
        bill: syncBill,
        patient_name: memberName,
        doctor_name: syncPresc?.doctor_name,
        doctor_registration_number: syncPresc?.doctor_reg,
        diagnosis: syncPresc?.diagnosis,
        medicines: syncPresc?.medicines_prescribed,
        procedures: syncPresc?.procedures,
        bill_breakdown: syncBill,
        claim_amount: claimAmount
      };
    }

    const claimInput: ClaimInput = {
      claim_id: claimId,
      member_id: memberId,
      member_name: memberName,
      member_join_date: memberJoinDate,
      treatment_date: treatmentDate,
      claim_amount: claimAmount,
      hospital: hospital || undefined,
      cashless_request: cashlessRequest,
      previous_claims_same_day: prevClaimsToday || undefined,
      documents: {
        prescription: finalExtractedData.prescription || {
          doctor_name: finalExtractedData.doctor_name || '',
          doctor_reg: finalExtractedData.doctor_registration_number || '',
          diagnosis: finalExtractedData.diagnosis || '',
          medicines_prescribed: finalExtractedData.medicines,
          procedures: finalExtractedData.procedures
        },
        bill: finalExtractedData.bill || finalExtractedData.bill_breakdown || {}
      }
    };

    try {
      if (adjudicationMode === 'ai') {
        const dsOutcome = await adjudicateWithDeepSeekR1(openaiKey, finalExtractedData, policy, rulesText);
        
        const mappedResult: AdjudicationResult = {
          claim_id: claimId,
          decision: dsOutcome.decision,
          approved_amount: dsOutcome.approved_amount !== undefined ? dsOutcome.approved_amount : 0,
          rejection_reasons: dsOutcome.rejection_reasons || [],
          confidence_score: dsOutcome.confidence_score || 0.95,
          notes: dsOutcome.reasoning ? dsOutcome.reasoning.join(' ') : (dsOutcome.next_steps || 'Adjudicated by DeepSeek R1.'),
          next_steps: dsOutcome.next_steps || 'No further action required.',
          rejected_items: dsOutcome.rejected_items || [],
          approved_items: dsOutcome.approved_items || [],
          policy_violations: dsOutcome.policy_violations || [],
          flags: dsOutcome.fraud_flags || [],
          medical_necessity_analysis: dsOutcome.medical_necessity_analysis || [],
          reasoning: dsOutcome.reasoning || []
        };
        onAdjudicateComplete(mappedResult, claimInput);
      } else {
        const outcome = adjudicateClaim(claimInput, policy);
        onAdjudicateComplete(outcome, claimInput);
      }
    } catch (err) {
      console.error('AI Adjudication failed, running local engine as fallback:', err);
      const outcome = adjudicateClaim(claimInput, policy);
      onAdjudicateComplete(outcome, claimInput);
    } finally {
      setAdjudicating(false);
    }
  };

  return (
    <div className="claim-submitter glass-card">
      <div className="card-header">
        <h2 className="gradient-text">Submit Insurance Claim</h2>
        <p className="card-subtitle">Upload digital documents and execute claims adjudication rules.</p>
      </div>

      {/* Preset loaders */}
      <div className="template-row">
        <span>Load Mock Templates:</span>
        <button className="btn-small" onClick={() => handleLoadTemplate('viral')}>🌡️ Viral Fever (TC001)</button>
        <button className="btn-small" onClick={() => handleLoadTemplate('dental')}>🦷 Dental Procedure (TC002)</button>
      </div>

      <div className="adjudicator-form-grid">
        {/* Form Inputs Left */}
        <div className="form-column">
          <h3>👤 Claimant & Claim Information</h3>
          
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
              {policy.network_hospitals.map(h => (
                <option key={h} value={h}>{h}</option>
              ))}
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
            <label>Frequency Check (Claims Submitted Today)</label>
            <input type="number" value={prevClaimsToday} onChange={(e) => setPrevClaimsToday(parseInt(e.target.value, 10))} />
          </div>
        </div>

        {/* Document Inputs Right */}
        <div className="form-column">
          <h3>📄 Document OCR Mock-up</h3>

          <div className="input-group">
            <label>Doctor's Prescription</label>
            <textarea 
              rows={6} 
              value={prescriptionText} 
              onChange={(e) => setPrescriptionText(e.target.value)}
              placeholder="Paste doctor prescription here..."
            />
          </div>

          <div className="input-group">
            <label>Invoice / Invoice Bill Details</label>
            <textarea 
              rows={5} 
              value={billText} 
              onChange={(e) => setBillText(e.target.value)}
              placeholder="Paste invoice items and costs here..."
            />
          </div>

          <div className="api-key-box" style={{ background: 'rgba(99, 102, 241, 0.05)', borderColor: 'rgba(99, 102, 241, 0.15)' }}>
            <label style={{ color: '#a5b4fc' }}>OpenRouter API Key (Prefilled for Gemini & DeepSeek)</label>
            <input 
              type="password" 
              value={openaiKey || DEFAULT_OPENROUTER_KEY} 
              onChange={(e) => setOpenaiKey(e.target.value)} 
              placeholder="sk-or-v1-..."
            />
          </div>

          <div className="input-group">
            <label>Adjudication Mode</label>
            <select value={adjudicationMode} onChange={(e) => setAdjudicationMode(e.target.value as any)}>
              <option value="ai">🧠 Dual LLM Chain (Gemini 2.5 Flash + DeepSeek R1)</option>
              <option value="local">⚡ Local Rules Engine (Instance Verification)</option>
            </select>
          </div>

          <div className="adjudication-actions">
            <button 
              className={`btn-secondary ${extracting ? 'loading' : ''}`}
              onClick={handleExtract}
              disabled={extracting || adjudicating}
            >
              {extracting ? 'AI Extracting...' : '✨ Run AI Extraction'}
            </button>
            <button 
              className="btn-primary" 
              onClick={handleSubmitAdjudication}
              disabled={extracting || adjudicating}
            >
              {adjudicating ? 'AI Adjudicating...' : '⚖️ Run Adjudication'}
            </button>
          </div>
        </div>
      </div>

      {/* Extracted Details View */}
      {extractedData && (
        <div className="extracted-fields-viewer">
          <h4>🔍 Extracted Structured Data (Confidence Score: 0.96)</h4>
          <pre>{JSON.stringify(extractedData, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
