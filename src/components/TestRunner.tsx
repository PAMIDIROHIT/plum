import React, { useState } from 'react';
import { TestCase, PolicyTerms, AdjudicationResult } from '../types';
import { adjudicateClaim } from '../utils/adjudicator';
import testCasesData from '../../test_cases.json';

interface TestRunnerProps {
  policy: PolicyTerms;
  onImportClaim: (claimInput: any) => void;
}

/**
 * TestRunner Component.
 * Executes the 10 built-in test scenarios from test_cases.json, verifying the rule engine's accuracy.
 * Displays interactive comparisons of actual results against expected decisions and approved amounts.
 */
export const TestRunner: React.FC<TestRunnerProps> = ({ policy, onImportClaim }) => {
  const testCases = (testCasesData.test_cases || []) as TestCase[];
  const [results, setResults] = useState<Record<string, AdjudicationResult>>({});
  const [running, setRunning] = useState(false);

  // Run a single test case
  const runTest = (tc: TestCase) => {
    const res = adjudicateClaim(tc.input_data, policy);
    setResults(prev => ({ ...prev, [tc.case_id]: res }));
  };

  // Run all test cases in the suite
  const runAllTests = () => {
    setRunning(true);
    const newResults: Record<string, AdjudicationResult> = {};
    testCases.forEach((tc) => {
      newResults[tc.case_id] = adjudicateClaim(tc.input_data, policy);
    });
    // Add a slight visual delay to feel premium
    setTimeout(() => {
      setResults(newResults);
      setRunning(false);
    }, 600);
  };

  // Check if actual matches expected
  const verifyResult = (tc: TestCase, actual?: AdjudicationResult) => {
    if (!actual) return null;
    const expectedDecision = tc.expected_output.decision;
    
    // Core decision matches
    const decisionMatches = actual.decision === expectedDecision;
    
    // Amount matches (if applicable)
    let amountMatches = true;
    if (tc.expected_output.approved_amount !== undefined) {
      amountMatches = actual.approved_amount === tc.expected_output.approved_amount;
    }
    
    // Rejections match (if applicable)
    let rejectionsMatch = true;
    if (tc.expected_output.rejection_reasons) {
      rejectionsMatch = tc.expected_output.rejection_reasons.every(r => actual.rejection_reasons.includes(r) || actual.decision === 'REJECTED');
    }

    return decisionMatches && amountMatches && rejectionsMatch;
  };

  // Calculate statistics
  const totalCases = testCases.length;
  const executedCases = Object.keys(results).length;
  const passedCases = testCases.filter(tc => verifyResult(tc, results[tc.case_id]) === true).length;

  return (
    <div className="test-runner glass-card">
      <div className="card-header flex-header">
        <div>
          <h2 className="gradient-text">Automated Test Suite</h2>
          <p className="card-subtitle">Verify adjudicator accuracy against the 10 reference scenarios in test_cases.json.</p>
        </div>
        <button 
          className={`btn-primary ${running ? 'loading' : ''}`}
          onClick={runAllTests}
          disabled={running}
        >
          {running ? 'Running Suite...' : '🚀 Run Test Suite'}
        </button>
      </div>

      {/* Stats Summary Panel */}
      {executedCases > 0 && (
        <div className="stats-panel">
          <div className="stat-card">
            <span className="stat-label">Total Executed</span>
            <span className="stat-value">{executedCases} / {totalCases}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Passed</span>
            <span className="stat-value text-success">{passedCases}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Failed</span>
            <span className="stat-value text-danger">{executedCases - passedCases}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Accuracy Rate</span>
            <span className="stat-value text-accent">
              {Math.round((passedCases / executedCases) * 100)}%
            </span>
          </div>
        </div>
      )}

      {/* Test Cases Table */}
      <div className="table-container">
        <table className="test-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Scenario Name</th>
              <th>Expected Outcome</th>
              <th>Actual Outcome</th>
              <th>Verification Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {testCases.map((tc) => {
              const actual = results[tc.case_id];
              const isPassed = verifyResult(tc, actual);

              return (
                <tr key={tc.case_id} className="test-row">
                  <td className="tc-id">{tc.case_id}</td>
                  <td>
                    <div className="tc-info">
                      <span className="tc-name">{tc.case_name}</span>
                      <span className="tc-desc">{tc.description}</span>
                    </div>
                  </td>
                  <td>
                    <div className="outcome-badge-container">
                      <span className={`status-badge badge-${tc.expected_output.decision.toLowerCase()}`}>
                        {tc.expected_output.decision}
                      </span>
                      {tc.expected_output.approved_amount !== undefined && (
                        <span className="amount-tag">₹{tc.expected_output.approved_amount}</span>
                      )}
                    </div>
                  </td>
                  <td>
                    {actual ? (
                      <div className="outcome-badge-container">
                        <span className={`status-badge badge-${actual.decision.toLowerCase()}`}>
                          {actual.decision}
                        </span>
                        <span className="amount-tag">₹{actual.approved_amount}</span>
                      </div>
                    ) : (
                      <span className="text-muted">Not run</span>
                    )}
                  </td>
                  <td>
                    {actual ? (
                      isPassed ? (
                        <span className="badge-pass">✅ Pass</span>
                      ) : (
                        <span className="badge-fail">❌ Discrepancy</span>
                      )
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button className="btn-small" onClick={() => runTest(tc)}>Run</button>
                      <button 
                        className="btn-small btn-secondary" 
                        onClick={() => onImportClaim(tc.input_data)}
                      >
                        Import
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
