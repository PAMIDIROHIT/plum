'use client';

import { useEffect } from 'react';

export default function GlobalError({ error, reset }) {
  useEffect(() => {
    console.error('Global unhandled exception:', error);
  }, [error]);

  return (
    <div className="dashboard-view" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <div className="glass-card" style={{ maxWidth: '500px', textAlign: 'center', padding: '40px' }}>
        <h2 className="text-danger" style={{ marginBottom: '16px', fontSize: '2rem' }}>⚠️ System Crash</h2>
        <p className="card-subtitle" style={{ marginBottom: '24px' }}>
          An unexpected rendering error occurred. The AI Pipeline might be returning malformed data.
        </p>
        
        <div className="error-banner" style={{ textAlign: 'left', wordBreak: 'break-all' }}>
          {error.message || "Unknown error"}
        </div>
        
        <button 
          className="btn-primary mt-4" 
          onClick={() => reset()}
          style={{ width: '100%' }}
        >
          🔄 Attempt Recovery
        </button>
      </div>
    </div>
  );
}
