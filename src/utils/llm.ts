import { DoctorPrescription, BillDetails } from '../types';

/**
 * Robust local fallback parser using Regular Expressions.
 * Extracts structured data from medical documents when no LLM API key is provided
 * or when the API calls fail. Handles formats specified in sample_documents_guide.md.
 */
export function localFallbackParser(text: string, type: 'prescription' | 'bill'): any {
  const normalized = text.replace(/\r\n/g, '\n');

  if (type === 'prescription') {
    const data: DoctorPrescription = {
      doctor_name: 'Unknown Doctor',
      doctor_reg: '',
      diagnosis: 'Not specified',
      medicines_prescribed: [],
      procedures: [],
      tests_prescribed: []
    };

    // Extract Doctor Name
    const docNameMatch = normalized.match(/Dr\.\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/i);
    if (docNameMatch) {
      data.doctor_name = `Dr. ${docNameMatch[1]}`;
    }

    // Extract Registration Number (Format: KA/12345/2015, DL/34567/2020 etc.)
    const regMatch = normalized.match(/Reg\.?\s*No:?\s*([A-Z0-9\/_-]+)/i);
    if (regMatch) {
      data.doctor_reg = regMatch[1].trim();
    } else {
      // Direct search for code patterns like MH/12345/2018
      const directRegMatch = normalized.match(/([A-Z]{2,4}\/\d{4,6}\/\d{4})/i);
      if (directRegMatch) {
        data.doctor_reg = directRegMatch[1].trim();
      }
    }

    // Extract Diagnosis
    const diagnosisMatch = normalized.match(/Diagnosis:\s*\n?([^\n\r]+)/i);
    if (diagnosisMatch) {
      data.diagnosis = diagnosisMatch[1].trim();
    }

    // Extract Medicines (Under Rx or Prescription)
    const rxSectionMatch = normalized.match(/Rx\s*\(Prescription\):([\s\S]*?)(?:Investigations|Advised|Follow-up|$)/i);
    if (rxSectionMatch) {
      const rxText = rxSectionMatch[1];
      const lines = rxText.split('\n');
      lines.forEach(line => {
        const medMatch = line.match(/^\d+\.?\s*(Tab\.|Syp\.|Cap\.|Tab|Syp|Cap)?\s*([A-Za-z0-9\s]+?)(?:\s+\d+|\s+x|\s*\[|$)/i);
        if (medMatch && medMatch[2].trim().length > 2) {
          data.medicines_prescribed?.push(medMatch[2].trim());
        }
      });
    }

    // Extract Procedures (Under Procedures or Diagnosis)
    const proceduresMatch = normalized.match(/Procedures?:\s*\n?([^\n\r]+)/i);
    if (proceduresMatch) {
      data.procedures = proceduresMatch[1].split(',').map(p => p.trim());
    }

    // If we see specific terms in text, populate accordingly
    if (normalized.toLowerCase().includes('root canal')) {
      data.procedures?.push('Root canal treatment');
    }
    if (normalized.toLowerCase().includes('whitening')) {
      data.procedures?.push('Teeth whitening');
    }
    if (normalized.toLowerCase().includes('panchakarma')) {
      data.treatment = 'Panchakarma therapy';
    }

    return data;
  } else {
    // Parser for Bill details
    const data: BillDetails = {};

    // Check for Consultation Fee
    const consultationMatch = normalized.match(/Consultation\s*Fee[s]?\s*₹?\s*(\d+)/i);
    if (consultationMatch) {
      data.consultation_fee = parseInt(consultationMatch[1], 10);
    }

    // Check for Medicines
    const medicinesMatch = normalized.match(/Medicines?\s*₹?\s*(\d+)/i);
    if (medicinesMatch) {
      data.medicines = parseInt(medicinesMatch[1], 10);
    }

    // Check for Root Canal
    const rootCanalMatch = normalized.match(/Root\s*Canal\s*(?:treatment)?\s*₹?\s*(\d+)/i);
    if (rootCanalMatch) {
      data.root_canal = parseInt(rootCanalMatch[1], 10);
    }

    // Check for Teeth Whitening
    const whiteningMatch = normalized.match(/Teeth\s*Whitening\s*₹?\s*(\d+)/i);
    if (whiteningMatch) {
      data.teeth_whitening = parseInt(whiteningMatch[1], 10);
    }

    // Check for Diagnostic Tests / Labs
    const diagMatch = normalized.match(/Diagnostic\s*Tests?:?\s*₹?\s*(\d+)/i);
    if (diagMatch) {
      data.diagnostic_tests = parseInt(diagMatch[1], 10);
    }

    // Check for MRI Scans
    const mriMatch = normalized.match(/MRI\s*(?:Scan|Spine)?\s*₹?\s*(\d+)/i);
    if (mriMatch) {
      data.mri_scan = parseInt(mriMatch[1], 10);
    }

    // Check for Therapy Charges
    const therapyMatch = normalized.match(/Therapy\s*(?:Charges)?\s*₹?\s*(\d+)/i);
    if (therapyMatch) {
      data.therapy_charges = parseInt(therapyMatch[1], 10);
    }

    // Check for Diet Plan
    const dietMatch = normalized.match(/Diet\s*Plan\s*₹?\s*(\d+)/i);
    if (dietMatch) {
      data.diet_plan = parseInt(dietMatch[1], 10);
    }

    return data;
  }
}

/**
 * Calls OpenAI GPT-4o-mini API using client-provided API Key.
 * Performs highly accurate structured data extraction from raw medical text/layouts.
 * 
 * @param apiKey - User's personal OpenAI API key.
 * @param text - The raw document text contents.
 * @param docType - Either 'prescription' or 'bill'.
 * @returns Promise<any> - The structured JSON matching the document type.
 */
export async function extractFromLLM(apiKey: string, text: string, docType: 'prescription' | 'bill'): Promise<any> {
  const systemPrompt = docType === 'prescription' 
    ? `You are an expert medical claims auditor. Analyze the following medical prescription text and extract a structured JSON object containing:
      - doctor_name (string, e.g. "Dr. Amit Sharma")
      - doctor_reg (string, registration format: "STATE/NUMBER/YEAR" like "KA/12345/2015", extract EXACTLY as written)
      - diagnosis (string, the clinical condition/diagnosis)
      - medicines_prescribed (array of strings, e.g., ["Paracetamol 650mg", "Amoxicillin"])
      - procedures (array of strings, if any surgical/dental procedures are advised)
      - treatment (string, any alternative medicine treatments like "Panchakarma")
      
      Return ONLY a valid JSON object. Do not include markdown code block syntax (like \`\`\`json).`
    : `You are an expert insurance bill auditor. Analyze the following medical invoice text and extract a structured JSON containing the cost of each line item. Identify values for:
      - consultation_fee (number)
      - diagnostic_tests (number)
      - medicines (number)
      - root_canal (number)
      - teeth_whitening (number)
      - mri_scan (number)
      - therapy_charges (number)
      - diet_plan (number)
      
      Only include the fields that have non-zero costs. Return ONLY a valid JSON object. Do not include markdown formatting.`;

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: text }
        ],
        temperature: 0.1,
        response_format: { type: 'json_object' }
      })
    });

    if (!response.ok) {
      const errorMsg = await response.text();
      throw new Error(`OpenAI API returned status ${response.status}: ${errorMsg}`);
    }

    const resJson = await response.json();
    const extractedText = resJson.choices[0].message.content;
    return JSON.parse(extractedText);
  } catch (error) {
    console.error('LLM extraction failed, using fallback regex parser:', error);
    // Graceful degradation: fallback to regex parser
    return localFallbackParser(text, docType);
  }
}
