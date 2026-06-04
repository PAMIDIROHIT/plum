import Navbar from '../components/Navbar';
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
          <Navbar />
          
          <main className="tab-window">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
