# 🌟 Plum AI OPD Claim Adjudication System

An intelligent, production-grade AI automation pipeline designed to process, extract, validate, and adjudicate Outpatient Department (OPD) medical claims using multimodal LLMs (Gemini 2.5 Flash Vision) and advanced reasoning engines (DeepSeek R1).

Built for the **Plum AI Automation Engineer Intern** assignment.

---
# video link
https://drive.google.com/file/d/1wK2hoiYClAAeyHsy-tXdFrTqclxUGwdO/view?usp=sharing

## 🎯 Executive Summary
This application transforms the highly manual, error-prone process of health insurance claim adjudication into a deterministic, AI-orchestrated pipeline. By combining the visual extraction power of **Gemini Vision** with the strict, step-by-step logic and reasoning of **DeepSeek R1**, the system achieves human-level auditing with complete mathematical enforcement of policy limits.

### ✨ Key Features
- **Multimodal OCR**: Upload medical prescriptions and invoices.
- **Dual-Engine Architecture**: 
  - *AI Chain*: DeepSeek R1 acts as a reasoning engine for complex semantic checks (Medical Necessity, Fraud Detection).
  - *Local Rules Engine*: A deterministic Python backend for instant, programmatic limit checks and sub-limit capping.
- **Explainable AI (XAI)**: A beautiful **Policy Validation Checklist** that translates raw JSON AI output into a sequential passed/bypassed/failed checklist for claims auditors.
- **Automated Test Suite**: A `/test-runner` dashboard to validate the deterministic rules engine instantly.

---

## 🏗️ System Architecture

The system is built using Domain-Driven Design (DDD) to isolate API routing, orchestration, LLM calling, and database persistence.

```mermaid
graph TD
    %% Styling
    classDef frontend fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff
    classDef backend fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff
    classDef ai fill:#8b5cf6,stroke:#5b21b6,stroke-width:2px,color:#fff
    classDef db fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff

    User((Claimant))
    UI[Next.js Frontend]:::frontend
    API[FastAPI Backend]:::backend
    
    User -->|Uploads Docs| UI
    UI -->|POST /claims/submit| API
    
    subgraph Adjudication Orchestrator
        API --> Extractor[Extraction Pipeline]
        Extractor --> Logic[Decision Router]
        Logic -->|AI Mode| AI_Engine[DeepSeek R1 Reasoning]
        Logic -->|Local Mode| Local_Engine[Deterministic Rules Engine]
    end
    
    Extractor -->|Images| Gemini[Gemini 2.5 Flash OCR]:::ai
    Gemini -->|Extracted JSON| Extractor
    
    AI_Engine <-->|Policy Terms| PolicyDB[(policy_terms.json)]
    Local_Engine <-->|Sub-limits/Caps| PolicyDB
    
    Logic --> Confidence[Confidence Scorer]
    Confidence --> DB[(SQLite Database)]:::db
    
    DB -->|Result| API
    API -->|Render Result| UI
```

---

## 🧠 Decision Logic Flowchart

```mermaid
flowchart TD
    classDef pass fill:#10b981,color:#fff,stroke:none
    classDef fail fill:#ef4444,color:#fff,stroke:none
    classDef review fill:#f59e0b,color:#fff,stroke:none
    classDef process fill:#3b82f6,color:#fff,stroke:none

    Start([Start Adjudication]) --> Elig{1. Eligibility Check}
    
    Elig -- Active --> Docs{2. Document Validity}
    Elig -- Inactive/Waiting --> Reject_Elig[REJECTED: Policy Inactive]:::fail
    
    Docs -- Valid --> Cov{3. Coverage & Exclusions}
    Docs -- Invalid/Mismatch --> Reject_Docs[REJECTED: Missing/Invalid]:::fail
    
    Cov -- Covered --> Lim{4. Limits & Sub-limits}
    Cov -- Cosmetic/Excluded --> Reject_Cov[REJECTED: Excluded Condition]:::fail
    
    Lim -- Within Limits --> Med{5. Medical Necessity}
    Lim -- Exceeds Per Claim --> Reject_Lim[REJECTED: Limit Exceeded]:::fail
    Lim -- Exceeds Annual --> Partial[PARTIAL APPROVAL: Capped]:::review
    
    Med -- Justified --> Fraud{6. Fraud & Security}
    Med -- Unjustified --> Reject_Med[REJECTED: Not Necessary]:::fail
    
    Fraud -- No Flags --> Approve[APPROVED: Ready for Payout]:::pass
    Fraud -- Anomalies/Duplicates --> Manual[MANUAL REVIEW]:::review
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Node.js (v18+)
- Python (v3.9+)
- API Keys for Google Gemini & OpenRouter (DeepSeek)

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env
echo "OPENROUTER_API_KEY=your_key_here" >> .env

# Run FastAPI Server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The application will be running at `http://localhost:3000`.

---

## 📁 Project Documentation
- 📄 **[API Documentation](./docs/api_documentation.md)**: Detailed API specs.
- 🤔 **[Assumptions](./docs/assumptions.md)**: Logic and architecture assumptions.
- 🧪 **[Test Cases](./assignment_docs/test_cases.json)**: Ground truth data.

---

## 🏆 Evaluation Highlights

| Criteria | Implementation Details |
|----------|------------------------|
| **AI Integration** | Extracts data with Gemini Vision and runs complex semantic logic using DeepSeek R1 Chain-of-Thought. |
| **Code Quality** | Pure Domain-Driven Design in Python. Modular `rule_engines`, `ai_pipelines`, and `adjudication` layers. |
| **User Experience** | Explainable AI UI that maps raw rejection codes into a readable checklist for non-technical claims adjusters. |
| **Bonus Features** | Multi-factor confidence scoring, dedicated automated test-runner suite, Local rule engine fallback. |

*Built for Plum's mission to protect 10M lives by 2025.* 💜
