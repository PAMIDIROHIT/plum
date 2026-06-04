'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar() {
  const pathname = usePathname();

  const getClassName = (path) => {
    // If path is dashboard, match exact or prefix, else match prefix
    if (path === '/dashboard') {
      return pathname === '/dashboard' || pathname === '/' ? 'tab-btn active' : 'tab-btn';
    }
    return pathname?.startsWith(path) ? 'tab-btn active' : 'tab-btn';
  };

  return (
    <nav className="navbar">
      <div className="logo-section">
        <h1>
          <span style={{ textTransform: 'lowercase', fontFamily: 'var(--font-heading)', fontWeight: '700', fontSize: '2rem' }}>plum</span>
          <span className="gradient-text" style={{ fontFamily: 'var(--font-sans)', fontWeight: '600', marginLeft: '6px', fontSize: '1.7rem' }}>adjudicate</span>
        </h1>
        <p>AI OPD Claim Adjudication Suite</p>
      </div>
      <div className="nav-tabs">
        <Link href="/dashboard" className={getClassName('/dashboard')}>
          📊 Dashboard
        </Link>
        <Link href="/upload" className={getClassName('/upload')}>
          ✍️ Submit Claim
        </Link>
        <Link href="/policy" className={getClassName('/policy')}>
          ⚙️ Policy Config
        </Link>
        <Link href="/test-runner" className={getClassName('/test-runner')}>
          🧪 Test Runner
        </Link>
      </div>
    </nav>
  );
}
