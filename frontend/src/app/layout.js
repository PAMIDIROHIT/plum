import Link from 'next/link';
import './globals.css';

export const metadata = {
  title: 'Plum Adjudicate - AI Claim Adjudicator',
  description: 'AI-powered OPD insurance claim adjudication and OCR engine.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="app-container">
          {/* Shared Navigation Header */}
          <nav className="navbar">
            <div className="logo-section">
              <h1>🛡️ <span className="gradient-text">Plum Adjudicate</span></h1>
              <p>AI OPD Claim Adjudication Suite</p>
            </div>
            <div className="nav-tabs">
              <Link href="/dashboard" className="tab-btn">
                📊 Dashboard
              </Link>
              <Link href="/upload" className="tab-btn">
                ✍️ Submit Claim
              </Link>
            </div>
          </nav>
          
          <main className="tab-window">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
