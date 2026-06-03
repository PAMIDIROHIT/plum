# FastAPI Backend API Documentation

This document describes the API endpoints provided by the FastAPI backend server. All payloads are communicated in JSON format.

---

## 1. Claims Operations

### Submit Claim / OCR Extraction
- **Endpoint**: `/api/claims/submit`
- **Method**: `POST`
- **Description**: Uploads raw prescription and bill text, runs Gemini 2.5 Flash for OCR parsing, executes adjudication (either local or via DeepSeek R1), and stores the result.
- **Request Body**:
  ```json
  {
    "member_id": "EMP001",
    "member_name": "Rajesh Kumar",
    "member_join_date": "2024-01-01",
    "treatment_date": "2024-11-01",
    "claim_amount": 1500,
    "hospital": "Apollo Hospitals",
    "cashless_request": true,
    "previous_claims_same_day": 0,
    "prescription_text": "...",
    "bill_text": "...",
    "adjudication_mode": "ai" 
  }
  ```
- **Response**: Returns the complete `AdjudicationResult` JSON payload.

### Retrieve Claims History
- **Endpoint**: `/api/claims/history`
- **Method**: `GET`
- **Description**: Fetches all claims stored in the local SQLite database.
- **Response**: List of claim records.

### Manual Update Claim Status
- **Endpoint**: `/api/claims/review`
- **Method**: `POST`
- **Description**: Updates a claim flagged with `MANUAL_REVIEW` to `APPROVED` or `REJECTED` by a supervisor.
- **Request Body**:
  ```json
  {
    "claim_id": "CLM_123456",
    "decision": "APPROVED",
    "notes": "Verified prescription authenticity."
  }
  ```

---

## 2. System Operations

### Health Check
- **Endpoint**: `/api/health`
- **Method**: `GET`
- **Description**: Verifies database connection state and server status.
