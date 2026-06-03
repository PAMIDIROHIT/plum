import { apiFetch } from './api';

/**
 * Service API layer connecting Next.js to FastAPI claim endpoints.
 */
export const claimService = {
  /**
   * Submits a claim along with document strings to trigger Gemini extraction and DeepSeek compliance checks.
   */
  submitClaim: async (claimData) => {
    return apiFetch('/claims/submit', {
      method: 'POST',
      body: JSON.stringify(claimData)
    });
  },

  /**
   * Fetches all processed claim records from the database history.
   */
  getClaimsHistory: async () => {
    return apiFetch('/claims/history');
  },

  /**
   * Allows claim managers to submit overrides on claims marked under MANUAL_REVIEW.
   */
  reviewClaim: async (claimId, decision, notes) => {
    return apiFetch('/claims/review', {
      method: 'POST',
      body: JSON.stringify({
        claim_id: claimId,
        decision,
        notes
      })
    });
  },

  /**
   * Checks status of the backend API service.
   */
  getHealth: async () => {
    return apiFetch('/health');
  },

  /**
   * Fetches active policy configuration from backend.
   */
  getPolicy: async () => {
    return apiFetch('/claims/policy');
  },

  /**
   * Saves updated policy configuration to backend.
   */
  updatePolicy: async (policyData) => {
    return apiFetch('/claims/policy', {
      method: 'POST',
      body: JSON.stringify(policyData)
    });
  },

  /**
   * Fetches the standard test cases from backend.
   */
  getTestCases: async () => {
    return apiFetch('/claims/test-cases');
  },

  /**
   * Submits a structured test case dictionary to backend test execution router.
   */
  runTestCase: async (testCase) => {
    return apiFetch('/claims/run-test', {
      method: 'POST',
      body: JSON.stringify(testCase)
    });
  }
};
