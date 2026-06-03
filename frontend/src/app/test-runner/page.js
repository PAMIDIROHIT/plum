'use client';

import { useState, useEffect } from 'react';
import { claimService } from '../../services/claimService';

/**
 * Automated Test Cases Runner component.
 * Loads 10 predefined test cases from test_cases.json and executes them sequentially
 * against the rules engine, comparing expected vs. actual outcomes.
 */
export default function TestRunnerPage() {
  const [testCases, setTestCases] = useState([]);
  const [results, setResults] = useState({});
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch test cases config from backend
  const fetchTestCases = async () => {
    try {
      setLoading(true);
      const data = await claimService.getTestCases();
      setTestCases(data.test_cases || []);
    } catch (e) {
      console.error('Failed to load test cases:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTestCases();
  }, []);

  // Run a single test case
  const runSingleTest = async (testCase) => {
    const caseId = testCase.case_id;
    setResults((prev) => ({
      ...prev,
      [caseId]: { running: true }
    }));

    try {
      const actual = await claimService.runTestCase(testCase);
      const expected = testCase.expected_output;

      // Verify pass conditions
      const decisionMatch = actual.decision === expected.decision;
      const approvedAmountMatch = Math.abs(actual.approved_amount - expected.approved_amount) < 0.01;
      const passed = decisionMatch && approvedAmountMatch;

      setResults((prev) => ({
        ...prev,
        [caseId]: {
          running: false,
          actual,
          passed,
          error: null
        }
      }));
      return passed;
    } catch (e) {
      setResults((prev) => ({
        ...prev,
        [caseId]: {
          running: false,
          actual: null,
          passed: false,
          error: e.message
        }
      }));
      return false;
    }
  };

  // Run all 10 test cases in sequence
  const runAllTests = async () => {
    setRunning(true);
    for (const testCase of testCases) {
      await runSingleTest(testCase);
    }
    setRunning(false);
  };

  if (loading) {
    return (
      <div className="glass-card empty-state">
        <p>Loading standard test cases...</p>
      </div>
    );
  }

  return (
    <div className="test-runner-view glass-card">
      <div className="card-header flex-header">
        <div>
          <h2 className="gradient-text">Automated Adjudication Test Suite</h2>
          <p className="card-subtitle">
            Execute verification scenarios against the rule engine to validate policy limits, waiting periods, and network discount calculations.
          </p>
        </div>
        <button 
          className="btn-primary" 
          onClick={runAllTests} 
          disabled={running || testCases.length === 0}
        >
          {running ? 'Running Suite...' : '🚀 Run Entire Test Suite'}
        </button>
      </div>

      <div className="table-container" style={{ marginTop: '24px' }}>
        <table className="claim-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Test Case Name</th>
              <th>Expected Outcome</th>
              <th>Actual Adjudication</th>
              <th>Verification Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {testCases.map((tc) => {
              const res = results[tc.case_id];
              const expected = tc.expected_output;
              
              return (
                <tr key={tc.case_id} className="claim-row">
                  <td className="claim-id-cell">{tc.case_id}</td>
                  <td>
                    <div className="member-info">
                      <span className="member-name">{tc.case_name}</span>
                      <span className="member-id-tag" style={{ fontSize: '0.8rem' }}>{tc.description}</span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span className={`status-badge badge-${expected.decision.toLowerCase()}`}>
                        {expected.decision}
                      </span>
                      <span className="amount-tag" style={{ width: 'fit-content' }}>
                        ₹{expected.approved_amount || 0} approved
                      </span>
                    </div>
                  </td>
                  <td>
                    {res ? (
                      res.running ? (
                        <span className="text-warning">Running...</span>
                      ) : res.error ? (
                        <span className="text-danger">Error: {res.error}</span>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          <span className={`status-badge badge-${res.actual.decision.toLowerCase()}`}>
                            {res.actual.decision}
                          </span>
                          <span className="amount-tag" style={{ width: 'fit-content' }}>
                            ₹{res.actual.approved_amount} approved
                          </span>
                        </div>
                      )
                    ) : (
                      <span className="text-muted">Not run</span>
                    )}
                  </td>
                  <td>
                    {res && !res.running && (
                      <span className={`status-badge ${res.passed ? 'badge-approved' : 'badge-rejected'}`}>
                        {res.passed ? 'PASS ✅' : 'FAIL ❌'}
                      </span>
                    )}
                  </td>
                  <td>
                    <button 
                      className="btn-small" 
                      onClick={() => runSingleTest(tc)}
                      disabled={running || (res && res.running)}
                    >
                      🔄 Run Case
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
