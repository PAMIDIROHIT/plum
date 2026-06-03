import { useState, useEffect } from 'react';
import type { PolicyTerms, ClaimInput, AdjudicationResult } from './types';
import { Dashboard } from './components/Dashboard';
import { ClaimSubmitter } from './components/ClaimSubmitter';
import { PolicyExplorer } from './components/PolicyExplorer';
import { TestRunner } from './components/TestRunner';
import initialPolicyData from '../policy_terms.json';

/**
 * Main App Component.
 * Orchestrates the overall application layout, manages the central state
 * (active tab, claims registry, customizable policy config, OpenAI API keys),
 * and coordinates data passing between sub-components.
 */
function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'submit' | 'policy' | 'tests'>('dashboard');
  
  // Custom policy state (defaults to policy_terms.json structure)
  const [policy, setPolicy] = useState<PolicyTerms>(initialPolicyData as any);
  
  // Central claims history log
  const [claims, setClaims] = useState<{ input: ClaimInput; result: AdjudicationResult }[]>([]);
  
  // Transferred claim payload from Test Suite to Submission Form
  const [importedClaim, setImportedClaim] = useState<ClaimInput | null>(null);

  // OpenAI secure local key state
  const [openaiKey, setOpenaiKey] = useState<string>('');

  // Load key from localStorage on mount
  useEffect(() => {
    const savedKey = localStorage.getItem('plum_openai_key');
    if (savedKey) {
      setOpenaiKey(savedKey);
    }
  }, []);

  // Save key to localStorage when updated
  const handleSetOpenaiKey = (key: string) => {
    setOpenaiKey(key);
    localStorage.setItem('plum_openai_key', key);
  };

  // Add processed claim to registry and focus Dashboard
  const handleAdjudicationComplete = (result: AdjudicationResult, rawClaim: ClaimInput) => {
    setClaims(prev => [{ input: rawClaim, result }, ...prev]);
    setImportedClaim(null); // Clear imported state
    setActiveTab('dashboard'); // Auto redirect to dashboard view
  };

  // Import a claim from test runner and redirect to claim submitter
  const handleImportClaim = (claimInput: ClaimInput) => {
    setImportedClaim(claimInput);
    setActiveTab('submit');
  };

  // Execute manual review action on a claim
  const handleReviewClaim = (claimId: string, decision: 'APPROVED' | 'REJECTED', notes: string) => {
    setClaims(prev => prev.map(c => {
      if (c.result.claim_id === claimId) {
        return {
          ...c,
          result: {
            ...c.result,
            decision,
            notes: `${c.result.notes} | Manual Review Note: ${notes}`,
            confidence_score: 1.0, // High confidence since verified by human
            next_steps: decision === 'APPROVED' 
              ? 'Claim manually approved. Reimbursement processing initiated.' 
              : 'Claim manually rejected. Notification sent to member.'
          }
        };
      }
      return c;
    }));
  };

  return (
    <div className="app-container">
      {/* Navigation Header */}
      <nav className="navbar">
        <div className="logo-section">
          <h1>🛡️ <span className="gradient-text">Plum Adjudicate</span></h1>
          <p>AI OPD Claim Adjudication Suite</p>
        </div>
        <div className="nav-tabs">
          <button 
            className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Dashboard ({claims.length})
          </button>
          <button 
            className={`tab-btn ${activeTab === 'submit' ? 'active' : ''}`}
            onClick={() => setActiveTab('submit')}
          >
            ✍️ Submit Claim
          </button>
          <button 
            className={`tab-btn ${activeTab === 'policy' ? 'active' : ''}`}
            onClick={() => setActiveTab('policy')}
          >
            ⚙️ Policy Config
          </button>
          <button 
            className={`tab-btn ${activeTab === 'tests' ? 'active' : ''}`}
            onClick={() => setActiveTab('tests')}
          >
            🧪 Test Runner
          </button>
        </div>
      </nav>

      {/* Main Tab Render Window */}
      <main className="tab-window">
        {activeTab === 'dashboard' && (
          <Dashboard claims={claims} onReviewClaim={handleReviewClaim} />
        )}
        
        {activeTab === 'submit' && (
          <ClaimSubmitter 
            policy={policy} 
            importedClaim={importedClaim}
            onAdjudicateComplete={handleAdjudicationComplete} 
            openaiKey={openaiKey}
            setOpenaiKey={handleSetOpenaiKey}
          />
        )}
        
        {activeTab === 'policy' && (
          <PolicyExplorer policy={policy} onUpdatePolicy={setPolicy} />
        )}
        
        {activeTab === 'tests' && (
          <TestRunner policy={policy} onImportClaim={handleImportClaim} />
        )}
      </main>
    </div>
  );
}

export default App;
