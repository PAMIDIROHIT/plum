/**
 * Types representing the data models for the Plum OPD Claim Adjudication Tool.
 */

export interface DoctorPrescription {
  doctor_name: string;
  doctor_reg: string;
  diagnosis: string;
  medicines_prescribed?: string[];
  procedures?: string[];
  treatment?: string;
  tests_prescribed?: string[];
}

export interface BillDetails {
  consultation_fee?: number;
  diagnostic_tests?: number;
  test_names?: string[];
  root_canal?: number;
  teeth_whitening?: number;
  medicines?: number;
  mri_scan?: number;
  therapy_charges?: number;
  diet_plan?: number;
  [key: string]: any; // Allow dynamic categories
}

export interface ClaimDocuments {
  prescription?: DoctorPrescription;
  bill: BillDetails;
}

export interface ClaimInput {
  claim_id?: string;
  member_id: string;
  member_name: string;
  member_join_date?: string; // Format: YYYY-MM-DD
  treatment_date: string; // Format: YYYY-MM-DD
  claim_amount: number;
  hospital?: string;
  cashless_request?: boolean;
  previous_claims_same_day?: number;
  documents: ClaimDocuments;
}

export interface AdjudicationResult {
  claim_id: string;
  decision: 'APPROVED' | 'REJECTED' | 'PARTIAL' | 'MANUAL_REVIEW';
  approved_amount: number;
  rejection_reasons: string[];
  confidence_score: number;
  notes: string;
  next_steps: string;
  // Extra detailed metadata to show audit logs in UI
  copay_applied?: number;
  network_discount_applied?: number;
  rejected_items?: string[];
  flags?: string[];
  cashless_approved?: boolean;
  limits_checked?: {
    category: string;
    limit: number;
    claimed: number;
    approved: number;
  }[];
}

export interface PolicyTerms {
  policy_id: string;
  policy_name: string;
  effective_date: string;
  policy_holder: {
    company: string;
    employees_covered: number;
    dependents_covered: boolean;
  };
  coverage_details: {
    annual_limit: number;
    per_claim_limit: number;
    family_floater_limit: number;
    consultation_fees: {
      covered: boolean;
      sub_limit: number;
      copay_percentage: number;
      network_discount: number;
    };
    diagnostic_tests: {
      covered: boolean;
      sub_limit: number;
      pre_authorization_required: boolean;
      covered_tests: string[];
    };
    pharmacy: {
      covered: boolean;
      sub_limit: number;
      generic_drugs_mandatory: boolean;
      branded_drugs_copay: number;
    };
    dental: {
      covered: boolean;
      sub_limit: number;
      routine_checkup_limit: number;
      procedures_covered: string[];
      cosmetic_procedures: boolean;
    };
    vision: {
      covered: boolean;
      sub_limit: number;
      eye_test_covered: boolean;
      glasses_contact_lenses: boolean;
      lasik_surgery: boolean;
    };
    alternative_medicine: {
      covered: boolean;
      sub_limit: number;
      covered_treatments: string[];
      therapy_sessions_limit: number;
    };
  };
  waiting_periods: {
    initial_waiting: number;
    pre_existing_diseases: number;
    maternity: number;
    specific_ailments: {
      diabetes: number;
      hypertension: number;
      joint_replacement: number;
      [key: string]: number;
    };
  };
  exclusions: string[];
  claim_requirements: {
    documents_required: string[];
    submission_timeline_days: number;
    minimum_claim_amount: number;
  };
  network_hospitals: string[];
  cashless_facilities: {
    available: boolean;
    network_only: boolean;
    pre_approval_required: boolean;
    instant_approval_limit: number;
  };
}

export interface TestCase {
  case_id: string;
  case_name: string;
  description: string;
  input_data: ClaimInput;
  expected_output: {
    decision: string;
    approved_amount?: number;
    rejection_reasons?: string[];
    rejected_items?: string[];
    notes?: string;
    flags?: string[];
    cashless_approved?: boolean;
    network_discount?: number;
    copay?: number;
    deductions?: {
      copay?: number;
    };
    confidence_score: number;
  };
}
