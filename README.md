# Plum OPD Claim Adjudication Tool

An AI-powered insurance claim adjudication engine and interactive dashboard built to automate the processing, extraction, validation, and decision reasoning of Outpatient Department (OPD) medical claims.

---

## 🚀 Key Features

1. **Dual LLM Chain Pipeline**:
   - **Gemini 2.5 Flash** (via OpenRouter): Executes high-accuracy OCR text structure parsing to extract patient metadata, doctor details, itemized bill breakdowns, and diagnosis details.
   - **DeepSeek R1** (via OpenRouter): Executes advanced cognitive insurance reasoning against policy terms, waiting periods, network discounts, exclusions, duplicate checks, and medical necessity.
2. **Interactive Adjudication Sandbox**:
   - Toggles between **⚡ Local Rules Engine** (real-time programmatic rules) and **🧠 Dual LLM Chain** (complete cognitive AI reasoning).
3. **Automated Test Runner Suite**:
   - One-click execution of the 10 reference scenarios in `test_cases.json`, comparing actual results side-by-side with expected decisions, approved amounts, and rejection codes.
4. **Dynamic Policy Configurator**:
   - Interactive console to edit coverage limits, copay percentages, waiting periods, and exclusions on-the-fly.
5. **Claims Audit & Review Desk**:
   - Visual metrics and detailed rules verification trail logs for every claim, with built-in supervisor workflows to manually approve/reject flagged claims.

---

## 🛠️ Technology Stack

- **Frontend**: React 19 + TypeScript + Vite
- **Styling**: Premium HSL-based Custom CSS (glassmorphic dark-mode, custom animations)
- **AI Core**: OpenRouter unified API (Gemini 2.5 Flash + DeepSeek R1)

---

## 📦 Folder Structure

```text
plum/
├── assignment_docs/          # Original assignment instructions and inputs
│   ├── ASSIGNMENT_README.md
│   ├── plum_intern_assignment.md
│   ├── policy_terms.json
│   ├── adjudication_rules.md
│   ├── test_cases.json
│   └── sample_documents_guide.md
├── src/
│   ├── components/           # UI Views (Dashboard, Submitter, Policy, TestRunner)
│   ├── types/                # TypeScript Interfaces
│   ├── utils/                # Adjudicator Rules Engine & OpenRouter API client
│   ├── App.tsx               # Primary App Layout & State Orchestrator
│   └── main.tsx
├── public/                   # Shared public assets
├── .env                      # Local environment secrets (ignored by Git)
├── package.json
└── README.md                 # Project Overview & Guide (This File)
```

---

## ⚙️ Getting Started

### Prerequisites
Ensure you have **Node.js** (v18+) and **npm** installed.

### Setup Instructions

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure OpenRouter API Key:
   The app reads your OpenRouter key from a local `.env` file. Create a `.env` file in the root folder:
   ```text
    VITE_OPENROUTER_KEY=your_openrouter_api_key_here
   ```
   *(Note: `.env` is listed in `.gitignore` and is never committed to keep credentials secure).*

3. Run the development server:
   ```bash
   npm run dev
   ```
   Open **[http://localhost:5173](http://localhost:5173)** in your browser.
