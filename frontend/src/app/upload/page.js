'use client';

import { useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { uploadDocument } from '../../services/api';
import { claimService } from '../../services/claimService';

// ─── Dynamic date helpers ──────────────────────────────────────────────────────
const today = () => new Date().toISOString().split('T')[0];
const daysAgo = (n) => { const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().split('T')[0]; };

// ─── Viral Fever Template ─────────────────────────────────────────────────────
const TMPL_PRESC_VIRAL = () => `--------------------------------
Dr. Rahul Sharma, MBBS MD
Reg. No: KA/45678/2015
Apollo Clinic, Bangalore
--------------------------------
Date: ${today()}

Patient Name: Rajesh Kumar
Age/Sex: 34/M

Diagnosis: Viral fever

Rx:
1. Tab. Paracetamol 650mg — 1-0-1 x 5 days
2. Tab. Vitamin C 500mg  — 0-1-0 x 10 days

Investigations Advised: CBC Test, Dengue test

Dr. Rahul Sharma`;

const TMPL_BILL_VIRAL = () => `--------------------------------
Apollo Clinic Invoice
GST: 29AAAAA1111A1Z1
--------------------------------
Patient: Rajesh Kumar
Date: ${today()}

PARTICULARS               AMOUNT
Consultation Fee          ₹ 1000
Diagnostic Tests (CBC)    ₹  500
TOTAL:                    ₹ 1500`;

// ─── Dental Template ──────────────────────────────────────────────────────────
const TMPL_PRESC_DENTAL = () => `--------------------------------
Dr. Neha Patel, MDS (Dentist)
Reg. No: MH/23456/2018
Patel Dental Care, Mumbai
--------------------------------
Date: ${today()}

Patient Name: Priya Singh
Age/Sex: 28/F

Diagnosis: Tooth decay — root canal + aesthetic enhancement
Rx: Root canal treatment, Teeth whitening

Dr. Neha Patel`;

const TMPL_BILL_DENTAL = () => `--------------------------------
Patel Dental Care
Date: ${today()}

Root Canal Treatment      ₹ 8000
Teeth Whitening           ₹ 4000
TOTAL:                    ₹ 12000`;

// ─── Pipeline Step Indicator ──────────────────────────────────────────────────
const STEPS = [
  { id: 'upload',      label: '📂 Upload',      desc: 'Document ingested' },
  { id: 'gemini',      label: '🔍 Gemini OCR',  desc: 'AI extraction running' },
  { id: 'rules',       label: '📋 Rule Engine', desc: 'Policy validation' },
  { id: 'deepseek',    label: '🧠 DeepSeek R1', desc: 'Adjudication reasoning' },
  { id: 'decision',    label: '⚖️ Decision',    desc: 'Final verdict' },
];

function PipelineProgress({ activeStep, result }) {
  const activeIdx = STEPS.findIndex(s => s.id === activeStep);
  return (
    <div className="pipeline-progress">
      {STEPS.map((step, i) => {
        const done = activeIdx > i || (activeStep === 'decision' && result);
        const active = activeIdx === i;
        return (
          <div key={step.id} className={`pipeline-step ${done ? 'done' : ''} ${active ? 'active' : ''}`}>
            <div className="step-dot">{done ? '✓' : i + 1}</div>
            <div className="step-info">
              <span className="step-label">{step.label}</span>
              {active && <span className="step-desc">{step.desc}…</span>}
            </div>
            {i < STEPS.length - 1 && <div className={`step-connector ${done ? 'done' : ''}`} />}
          </div>
        );
      })}
    </div>
  );
}

// ─── Gemini Extraction Preview ───────────────────────────────────────────────
function GeminiExtractionPreview({ data, label }) {
  if (!data) return null;
  const hasContent = data.doctor_name || data.diagnosis || data.medicines?.length ||
    data.bill_breakdown || data.hospital_or_clinic;
  if (!hasContent) return null;

  return (
    <div style={{
      marginTop: 8, padding: '12px 14px',
      background: 'rgba(66,133,244,0.08)', border: '1px solid rgba(66,133,244,0.25)',
      borderRadius: 10
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{
          background: 'linear-gradient(135deg,#4285F4,#34A853)', color: '#fff',
          padding: '2px 8px', borderRadius: 6, fontSize: '0.72rem', fontWeight: 700
        }}>✦ Gemini 2.5 Flash</span>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{label} — Extracted Data</span>
        {data.ocr_confidence != null && (
          <span style={{
            marginLeft: 'auto', fontSize: '0.72rem', fontWeight: 700,
            color: data.ocr_confidence >= 0.8 ? '#4ade80' : data.ocr_confidence >= 0.6 ? '#facc15' : '#f87171'
          }}>OCR {Math.round(data.ocr_confidence * 100)}%</span>
        )}
      </div>
      <div style={{ display: 'grid', gap: 6 }}>
        {data.doctor_name && (
          <p style={{ margin: 0, fontSize: '0.82rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>🩺 Doctor: </span>
            <strong>{data.doctor_name}</strong>
            {data.doctor_registration_number && <span style={{ color: 'var(--text-muted)', marginLeft: 6 }}>({data.doctor_registration_number})</span>}
          </p>
        )}
        {data.hospital_or_clinic && (
          <p style={{ margin: 0, fontSize: '0.82rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>🏥 Clinic: </span><strong>{data.hospital_or_clinic}</strong>
          </p>
        )}
        {data.diagnosis && (
          <p style={{ margin: 0, fontSize: '0.82rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>🔬 Diagnosis: </span>
            <strong style={{ color: 'var(--accent)' }}>{data.diagnosis}</strong>
          </p>
        )}
        {data.medicines?.length > 0 && (
          <p style={{ margin: 0, fontSize: '0.82rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>💊 Medicines: </span>
            {data.medicines.join(', ')}
          </p>
        )}
        {data.claim_amount > 0 && (
          <p style={{ margin: 0, fontSize: '0.82rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>💰 Total Amount: </span>
            <strong style={{ color: '#4ade80' }}>₹{data.claim_amount?.toLocaleString('en-IN')}</strong>
          </p>
        )}
        {data.bill_breakdown && Object.keys(data.bill_breakdown).length > 0 && (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Bill items: {Object.entries(data.bill_breakdown).map(([k, v]) => `${k.replace(/_/g, ' ')}: ₹${v}`).join(' | ')}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Policy Validation Checklist ──────────────────────────────────────────────
function PolicyValidationChecklist({ result }) {
  const rejections = result.rejection_reasons || [];
  const flags = result.flags || [];

  const hasRej = (codes) => codes.some(c => rejections.includes(c));
  const getRej = (codes) => codes.filter(c => rejections.includes(c)).join(', ').replace(/_/g, ' ');

  // Catch-all for any unknown rejection reasons the model might hallucinate
  const knownCodes = ['POLICY_INACTIVE', 'WAITING_PERIOD', 'MEMBER_NOT_COVERED', 'MISSING_DOCUMENTS', 'ILLEGIBLE_DOCUMENTS', 'INVALID_PRESCRIPTION', 'DOCTOR_REG_INVALID', 'DATE_MISMATCH', 'PATIENT_MISMATCH', 'SERVICE_NOT_COVERED', 'EXCLUDED_CONDITION', 'PRE_AUTH_MISSING', 'ANNUAL_LIMIT_EXCEEDED', 'SUB_LIMIT_EXCEEDED', 'PER_CLAIM_EXCEEDED', 'BELOW_MIN_AMOUNT', 'NOT_MEDICALLY_NECESSARY', 'EXPERIMENTAL_TREATMENT', 'COSMETIC_PROCEDURE'];
  const unknownRejections = rejections.filter(r => !knownCodes.includes(r));

  const failElig = hasRej(['POLICY_INACTIVE', 'WAITING_PERIOD', 'MEMBER_NOT_COVERED']);
  const failDocs = hasRej(['MISSING_DOCUMENTS', 'ILLEGIBLE_DOCUMENTS', 'INVALID_PRESCRIPTION', 'DOCTOR_REG_INVALID', 'DATE_MISMATCH', 'PATIENT_MISMATCH']);
  const failCov  = hasRej(['SERVICE_NOT_COVERED', 'EXCLUDED_CONDITION', 'PRE_AUTH_MISSING']);
  const failLim  = hasRej(['ANNUAL_LIMIT_EXCEEDED', 'SUB_LIMIT_EXCEEDED', 'PER_CLAIM_EXCEEDED', 'BELOW_MIN_AMOUNT']);
  const failMed  = hasRej(['NOT_MEDICALLY_NECESSARY', 'EXPERIMENTAL_TREATMENT', 'COSMETIC_PROCEDURE']);
  const failUnknown = unknownRejections.length > 0;

  const statusElig = failElig ? 'failed' : 'passed';
  const statusDocs = failElig ? 'bypassed' : (failDocs ? 'failed' : 'passed');
  const statusCov  = (failElig || failDocs) ? 'bypassed' : (failCov ? 'failed' : 'passed');
  const statusLim  = (failElig || failDocs || failCov) ? 'bypassed' : (failLim ? 'failed' : 'passed');
  const statusMed  = (failElig || failDocs || failCov) ? 'bypassed' : (failMed ? 'failed' : 'passed');
  const statusFraud = (failElig || failDocs || failCov) ? 'bypassed' : (flags.length > 0 ? 'flagged' : 'passed');

  const CheckRow = ({ title, status, reason, icon }) => {
    const config = {
      passed:   { icon: '✅', color: '#4ade80', text: 'Passed', bg: 'rgba(74,222,128,0.15)' },
      failed:   { icon: '❌', color: '#f87171', text: 'Failed', bg: 'rgba(248,113,113,0.15)' },
      flagged:  { icon: '⚠️', color: '#facc15', text: 'Flagged', bg: 'rgba(250,204,21,0.15)' },
      bypassed: { icon: '⏭️', color: 'var(--text-muted)', text: 'Bypassed', bg: 'rgba(255,255,255,0.05)' },
    }[status];

    return (
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <span style={{ fontSize: '1.1rem', marginTop: 1 }}>{config.icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong style={{ fontSize: '0.85rem', color: status === 'bypassed' ? 'var(--text-muted)' : 'var(--text-primary)' }}>
              {icon} {title}
            </strong>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', color: config.color, background: config.bg, padding: '2px 8px', borderRadius: 12 }}>
              {config.text}
            </span>
          </div>
          {(status === 'failed' || status === 'flagged') && reason && (
            <div style={{ color: config.color, fontSize: '0.8rem', marginTop: 6, lineHeight: 1.4 }}>Reason: {reason}</div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div style={{ marginTop: 16, padding: '14px 18px', background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12 }}>
      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
        📋 Policy Validation Checklist
      </div>
      <CheckRow title="Eligibility & Waiting Period" status={statusElig} reason={getRej(['POLICY_INACTIVE', 'WAITING_PERIOD', 'MEMBER_NOT_COVERED'])} icon="👤" />
      <CheckRow title="Document Validity & Authenticity" status={statusDocs} reason={getRej(['MISSING_DOCUMENTS', 'ILLEGIBLE_DOCUMENTS', 'INVALID_PRESCRIPTION', 'DOCTOR_REG_INVALID', 'DATE_MISMATCH', 'PATIENT_MISMATCH'])} icon="📄" />
      <CheckRow title="Coverage & Exclusions" status={statusCov} reason={getRej(['SERVICE_NOT_COVERED', 'EXCLUDED_CONDITION', 'PRE_AUTH_MISSING'])} icon="☂️" />
      <CheckRow title="Limits & Sub-limits" status={statusLim} reason={getRej(['ANNUAL_LIMIT_EXCEEDED', 'SUB_LIMIT_EXCEEDED', 'PER_CLAIM_EXCEEDED', 'BELOW_MIN_AMOUNT'])} icon="💰" />
      <CheckRow title="Medical Necessity" status={statusMed} reason={getRej(['NOT_MEDICALLY_NECESSARY', 'EXPERIMENTAL_TREATMENT', 'COSMETIC_PROCEDURE'])} icon="⚕️" />
      <CheckRow title="Fraud & Security Analysis" status={statusFraud} reason={flags.join(', ')} icon="🛡️" />
      
      {failUnknown && (
        <CheckRow title="Other Rules" status="failed" reason={unknownRejections.join(', ').replace(/_/g, ' ')} icon="⚙️" />
      )}
    </div>
  );
}

// ─── Decision Result Card ─────────────────────────────────────────────────────
function DecisionCard({ result, onNewClaim }) {
  const decisionColor = {
    APPROVED: 'var(--success)',
    PARTIAL: 'var(--warning)',
    REJECTED: 'var(--danger)',
    MANUAL_REVIEW: '#8b5cf6',
  }[result.decision] || 'var(--text-muted)';

  const ext = result.extraction_data;

  return (
    <div className="decision-card glass-card">
      <div className="decision-header">
        <span className="decision-label" style={{ color: decisionColor }}>
          {result.decision === 'APPROVED' && '✅'}
          {result.decision === 'PARTIAL' && '⚠️'}
          {result.decision === 'REJECTED' && '❌'}
          {result.decision === 'MANUAL_REVIEW' && '🔎'}
          {' '}{result.decision}
        </span>
        <span className="decision-amount">
          ₹{result.approved_amount?.toLocaleString('en-IN') ?? 0} approved
        </span>
      </div>

      <div className="decision-grid">
        <div>
          <span className="decision-meta-label">Claim ID</span>
          <span className="decision-meta-value">{result.claim_id}</span>
        </div>
        <div>
          <span className="decision-meta-label">AI Confidence</span>
          <span className="decision-meta-value">{Math.round((result.confidence_score ?? 0) * 100)}%</span>
        </div>
        <div>
          <span className="decision-meta-label">Workflow State</span>
          <span className="decision-meta-value">{result.workflow_state ?? '—'}</span>
        </div>
        {result.copay_applied > 0 && (
          <div>
            <span className="decision-meta-label">Copay Deducted</span>
            <span className="decision-meta-value">₹{result.copay_applied}</span>
          </div>
        )}
        {result.network_discount_applied > 0 && (
          <div>
            <span className="decision-meta-label">Network Discount</span>
            <span className="decision-meta-value">₹{result.network_discount_applied}</span>
          </div>
        )}
      </div>

      {/* Gemini Extraction Summary in Decision Card */}
      {ext && (ext.doctor_name || ext.diagnosis || ext.medicines?.length > 0) && (
        <div style={{
          marginTop: 12, padding: '10px 14px',
          background: 'rgba(66,133,244,0.08)', border: '1px solid rgba(66,133,244,0.2)',
          borderRadius: 8
        }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            ✦ Gemini 2.5 Flash — Extracted Document Data
          </div>
          {ext.doctor_name && <p style={{ margin: '2px 0', fontSize: '0.82rem' }}><span style={{ color: 'var(--text-muted)' }}>Doctor: </span><strong>{ext.doctor_name}</strong></p>}
          {ext.diagnosis && <p style={{ margin: '2px 0', fontSize: '0.82rem' }}><span style={{ color: 'var(--text-muted)' }}>Diagnosis: </span><strong style={{ color: 'var(--accent)' }}>{ext.diagnosis}</strong></p>}
          {ext.medicines?.length > 0 && <p style={{ margin: '2px 0', fontSize: '0.82rem' }}><span style={{ color: 'var(--text-muted)' }}>Medicines: </span>{ext.medicines.join(', ')}</p>}
          {ext.hospital_or_clinic && <p style={{ margin: '2px 0', fontSize: '0.82rem' }}><span style={{ color: 'var(--text-muted)' }}>Clinic: </span>{ext.hospital_or_clinic}</p>}
        </div>
      )}

      {/* ── Beautiful Policy Checklist ── */}
      <PolicyValidationChecklist result={result} />

      {result.notes && <p className="decision-notes" style={{ marginTop: 16 }}><strong>Notes:</strong> {result.notes}</p>}
      {result.next_steps && <p className="decision-notes"><strong>Next Steps:</strong> {result.next_steps}</p>}

      {result.reasoning?.length > 0 && (
        <details className="decision-reasoning">
          <summary>🧠 DeepSeek R1 Adjudication Reasoning</summary>
          <ol style={{ paddingLeft: 20, marginTop: 8, lineHeight: 1.7 }}>
            {result.reasoning.map((r, i) => <li key={i} style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 4 }}>{r}</li>)}
          </ol>
        </details>
      )}

      <div className="decision-actions">
        <button className="btn-small" onClick={onNewClaim}>+ Submit Another Claim</button>
        <button className="btn-small" onClick={() => window.location.href = '/dashboard'}>📊 View Dashboard</button>
      </div>
    </div>
  );
}

// ─── FileDropZone Component ───────────────────────────────────────────────────
function FileDropZone({ label, icon, onExtracted }) {
  const inputRef = useRef(null);
  const [state, setState] = useState('idle'); // idle | uploading | done | error
  const [fileName, setFileName] = useState(null);
  const [quality, setQuality] = useState(null);
  const [geminiData, setGeminiData] = useState(null);

  const processFile = useCallback(async (file) => {
    setState('uploading');
    setFileName(file.name);
    setGeminiData(null);
    try {
      const result = await uploadDocument(file);
      setQuality(result.quality_assessment);
      setGeminiData(result.gemini_extraction || null);
      // Pass extracted text + Gemini structured data to parent
      onExtracted(
        result.extracted_text || '',
        result.gemini_extraction || null,
        result
      );
      setState('done');
    } catch (e) {
      console.error('Upload failed:', e);
      setState('error');
    }
  }, [onExtracted]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }, [processFile]);

  const reset = () => { setState('idle'); setFileName(null); setQuality(null); setGeminiData(null); };

  return (
    <div className="upload-zone-wrapper">
      <label className="zone-label">{icon} {label}</label>
      <div
        className={`file-drop-zone status-${state}`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => state !== 'uploading' && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.tif,.webp"
          style={{ display: 'none' }}
          onChange={(e) => { const f = e.target.files[0]; if (f) processFile(f); }}
        />
        <div className="drop-zone-content">
          {state === 'idle' && <>
            <span className="drop-icon">{icon}</span>
            <span className="drop-label">Drag & drop or click to upload</span>
            <span className="drop-hint">PDF, JPG, PNG, TIFF, WebP — max 10 MB</span>
          </>}
          {state === 'uploading' && <>
            <span className="drop-icon spin">⏳</span>
            <span className="drop-label">Processing {fileName}…</span>
            <span className="drop-hint">Gemini 2.5 Flash Vision extracting…</span>
          </>}
          {state === 'done' && <>
            <span className="drop-icon">✅</span>
            <span className="drop-label">{fileName}</span>
            {quality && (
              <span className={`quality-badge ${quality.is_legible ? 'good' : 'warn'}`}>
                OCR quality: {Math.round(quality.quality_score * 100)}%
                {quality.issues?.length > 0 ? ` — ${quality.issues[0]}` : ' — Good'}
              </span>
            )}
            <span className="drop-hint" style={{ marginTop: 6 }}>Click to replace</span>
          </>}
          {state === 'error' && <>
            <span className="drop-icon">❌</span>
            <span className="drop-label">Upload failed — {fileName}</span>
            <span className="drop-hint">Click to retry</span>
          </>}
        </div>
      </div>
      {/* Show Gemini extraction preview below the drop zone */}
      {state === 'done' && geminiData && (
        <GeminiExtractionPreview data={geminiData} label={label} />
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function UploadPage() {
  const router = useRouter();

  // Form state
  const [memberId, setMemberId]             = useState('EMP101');
  const [memberName, setMemberName]         = useState('John Doe');
  const [memberJoinDate, setMemberJoinDate] = useState(daysAgo(200));
  const [treatmentDate, setTreatmentDate]   = useState(today());
  const [claimAmount, setClaimAmount]       = useState(1500);
  const [hospital, setHospital]             = useState('');
  const [cashless, setCashless]             = useState(false);
  const [prevClaims, setPrevClaims]         = useState(0);
  const [prescText, setPrescText]           = useState(TMPL_PRESC_VIRAL());
  const [billText, setBillText]             = useState(TMPL_BILL_VIRAL());
  const [adjMode, setAdjMode]               = useState('ai');
  const [inputMode, setInputMode]           = useState('paste');

  // Pipeline state
  const [pipelineStep, setPipelineStep]   = useState(null);
  const [adjudicating, setAdjudicating]   = useState(false);
  const [result, setResult]               = useState(null);
  const [error, setError]                 = useState(null);

  // ─── Template loader ───────────────────────────────────────────────────────
  const loadTemplate = (type) => {
    if (type === 'viral') {
      setMemberName('Rajesh Kumar'); setMemberId('EMP001');
      setTreatmentDate(today()); setMemberJoinDate(daysAgo(200)); setClaimAmount(1500);
      setPrescText(TMPL_PRESC_VIRAL()); setBillText(TMPL_BILL_VIRAL());
    } else {
      setMemberName('Priya Singh'); setMemberId('EMP002');
      setTreatmentDate(today()); setMemberJoinDate(daysAgo(200)); setClaimAmount(12000);
      setPrescText(TMPL_PRESC_DENTAL()); setBillText(TMPL_BILL_DENTAL());
    }
    setResult(null); setError(null); setPipelineStep(null);
  };

  // ─── File upload handlers ──────────────────────────────────────────────────
  const handlePrescExtracted = useCallback((text, geminiData) => {
    setPrescText(text);
    // Auto-fill patient name from Gemini extraction
    if (geminiData?.patient_name && geminiData.patient_name !== 'Unknown') {
      setMemberName(geminiData.patient_name);
    }
    if (geminiData?.treatment_date) setTreatmentDate(geminiData.treatment_date);
  }, []);

  const handleBillExtracted = useCallback((text, geminiData) => {
    setBillText(text);
    // Auto-fill claim amount from Gemini invoice extraction
    if (geminiData?.claim_amount && geminiData.claim_amount > 0) {
      setClaimAmount(geminiData.claim_amount);
    } else if (geminiData?.bill_breakdown) {
      // Fallback: sum bill breakdown values if claim_amount not extracted
      const sum = Object.values(geminiData.bill_breakdown)
        .reduce((acc, v) => acc + (typeof v === 'number' ? v : 0), 0);
      if (sum > 0) setClaimAmount(sum);
    }
    if (geminiData?.hospital_or_clinic) setHospital(geminiData.hospital_or_clinic);
  }, []);

  // ─── Submit ────────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!prescText.trim()) { setError('Please provide a prescription (upload or paste text).'); return; }
    if (!billText.trim())  { setError('Please provide a bill/invoice (upload or paste text).'); return; }

    setError(null);
    setResult(null);
    setAdjudicating(true);

    try {
      // Visual pipeline step progression
      setPipelineStep('upload');
      await new Promise(r => setTimeout(r, 400));

      setPipelineStep('gemini');
      const payload = {
        member_id: memberId,
        member_name: memberName,
        member_join_date: memberJoinDate,
        treatment_date: treatmentDate,
        claim_amount: parseFloat(claimAmount) || 0,
        hospital: hospital || null,
        cashless_request: cashless,
        previous_claims_same_day: parseInt(prevClaims) || 0,
        prescription_text: prescText,
        bill_text: billText,
        adjudication_mode: adjMode,
      };

      // Show rule engine step briefly
      await new Promise(r => setTimeout(r, 300));
      setPipelineStep('rules');
      await new Promise(r => setTimeout(r, 300));
      setPipelineStep('deepseek');

      const outcome = await claimService.submitClaim(payload);

      setPipelineStep('decision');
      await new Promise(r => setTimeout(r, 200));
      setResult(outcome);
    } catch (e) {
      console.error(e);
      setError('Adjudication failed: ' + e.message);
      setPipelineStep(null);
    } finally {
      setAdjudicating(false);
    }
  };

  const handleNewClaim = () => {
    setResult(null); setError(null); setPipelineStep(null);
  };

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="claim-submitter glass-card">
      <div className="card-header">
        <h2 className="gradient-text">Submit Insurance Claim</h2>
        <p className="card-subtitle">
          Upload real medical documents or paste text — processed by Gemini 2.5 Flash Vision + DeepSeek R1
        </p>
      </div>

      {/* Template row */}
      <div className="template-row">
        <span>Load Mock Templates:</span>
        <button className="btn-small" onClick={() => loadTemplate('viral')}>🌡️ Viral Fever (TC001)</button>
        <button className="btn-small" onClick={() => loadTemplate('dental')}>🦷 Dental Procedure (TC002)</button>
      </div>

      {/* Pipeline progress (shown while processing) */}
      {(adjudicating || result) && pipelineStep && (
        <PipelineProgress activeStep={pipelineStep} result={result} />
      )}

      {/* Result card (shown after decision) */}
      {result && <DecisionCard result={result} onNewClaim={handleNewClaim} />}

      {/* Error state */}
      {error && (
        <div className="error-banner">⚠️ {error}</div>
      )}

      {/* Main form — hidden while showing result */}
      {!result && (
        <div className="adjudicator-form-grid">
          {/* ── Left: Patient & Provider ── */}
          <div className="form-column">
            <h3>👤 Patient & Provider Details</h3>

            <div className="input-group">
              <label>Member ID</label>
              <input type="text" value={memberId} onChange={e => setMemberId(e.target.value)} />
            </div>
            <div className="input-group">
              <label>Patient Name</label>
              <input type="text" value={memberName} onChange={e => setMemberName(e.target.value)} />
            </div>
            <div className="dual-inputs">
              <div className="input-group">
                <label>Join Date</label>
                <input type="date" value={memberJoinDate} onChange={e => setMemberJoinDate(e.target.value)} />
              </div>
              <div className="input-group">
                <label>Treatment Date</label>
                <input type="date" value={treatmentDate} onChange={e => setTreatmentDate(e.target.value)} />
              </div>
            </div>
            <div className="input-group">
              <label>Claim Amount (₹)</label>
              <input type="number" value={claimAmount} onChange={e => setClaimAmount(e.target.value)} />
            </div>
            <div className="input-group">
              <label>Provider / Hospital</label>
              <select value={hospital} onChange={e => setHospital(e.target.value)}>
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
                <input type="checkbox" checked={cashless} onChange={e => setCashless(e.target.checked)} />
                <span className="slider round"></span>
              </label>
              <span>Request Cashless Adjudication</span>
            </div>
            <div className="input-group">
              <label>Claims Submitted Today</label>
              <input type="number" value={prevClaims} onChange={e => setPrevClaims(e.target.value)} />
            </div>
            <div className="input-group">
              <label>Adjudication Mode</label>
              <select value={adjMode} onChange={e => setAdjMode(e.target.value)}>
                <option value="ai">🧠 AI Chain — Gemini 2.5 Flash + DeepSeek R1</option>
                <option value="local">⚡ Local Rules Engine — Offline / Fast</option>
              </select>
            </div>
          </div>

          {/* ── Right: Documents ── */}
          <div className="form-column">
            <h3>📄 Medical Documents</h3>

            {/* Input mode tabs */}
            <div className="input-mode-tabs">
              <button className={`mode-tab ${inputMode === 'upload' ? 'active' : ''}`} onClick={() => setInputMode('upload')}>
                📎 Upload Files
              </button>
              <button className={`mode-tab ${inputMode === 'paste' ? 'active' : ''}`} onClick={() => setInputMode('paste')}>
                ✏️ Paste Text
              </button>
            </div>

            {/* Upload mode */}
            {inputMode === 'upload' && (
              <div className="upload-zones">
                <FileDropZone
                  label="Doctor's Prescription"
                  icon="📋"
                  onExtracted={handlePrescExtracted}
                />
                <FileDropZone
                  label="Invoice / Medical Bill"
                  icon="🧾"
                  onExtracted={handleBillExtracted}
                />

              </div>
            )}

            {/* Paste text mode */}
            {inputMode === 'paste' && (
              <>
                <div className="input-group">
                  <label>Doctor's Prescription (Text)</label>
                  <textarea rows={8} value={prescText} onChange={e => setPrescText(e.target.value)} placeholder="Paste prescription text…" />
                </div>
                <div className="input-group">
                  <label>Invoice / Bill (Text)</label>
                  <textarea rows={6} value={billText} onChange={e => setBillText(e.target.value)} placeholder="Paste invoice / bill text…" />
                </div>
              </>
            )}

            <div className="adjudication-actions" style={{ gridTemplateColumns: '1fr' }}>
              <button className="btn-primary" onClick={handleSubmit} disabled={adjudicating}>
                {adjudicating ? '⏳ Running AI Pipeline…' : '⚖️ Submit Claim for Adjudication'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
