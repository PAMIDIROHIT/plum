# System Assumptions & Boundary Conditions

This document outlines the list of core assumptions made during the design and development of the OPD Claim Adjudication Suite.

1. **Document Format**:
   - Since actual image files and PDF attachments require complex cloud OCR setups, we assume medical documents (prescriptions/invoices) are simulated by text segments. 
   - A robust regex parser extracts key values as a zero-cost local fallback if external LLM APIs fail.

2. **Claim Eligibility & Join Dates**:
   - If a member's joining date is omitted in the claim, we assume they have satisfied the initial waiting period (30 days) and all specific ailment waiting periods (90+ days).

3. **Copays & Network Discounts**:
   - Network discount of 20% applies to the total claim amount if the provider matches the list of network hospitals in `policy_terms.json`.
   - Copay of 10% is applied to consultation fees under standard policy, but is adjusted dynamically when custom config settings override them.

4. **Fraud Indicators**:
   - Claims are flagged for manual review if more than 2 claims are submitted by the same member on the same treatment date.
   - Large claims above ₹25,000 are escalated automatically to supervisor review.
