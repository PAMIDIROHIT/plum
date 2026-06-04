const BASE_URL = 'http://localhost:8000/api';

/**
 * Clean HTTP client fetch wrapper pointing to the backend API port.
 *
 * IMPORTANT: When body is FormData (file uploads), do NOT set Content-Type.
 * The browser will automatically set it to multipart/form-data with the correct
 * boundary — overriding it breaks multipart parsing in FastAPI.
 */
export async function apiFetch(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;

  // Only set Content-Type for JSON bodies — let browser handle FormData automatically
  const isFormData = options.body instanceof FormData;
  const headers = isFormData
    ? { ...(options.headers || {}) }
    : { 'Content-Type': 'application/json', ...(options.headers || {}) };

  const config = {
    ...options,
    headers,
  };

  const response = await fetch(url, config);
  if (!response.ok) {
    let errorMsg;
    try {
      const errJson = await response.json();
      errorMsg = errJson.detail || JSON.stringify(errJson);
    } catch {
      errorMsg = await response.text();
    }
    throw new Error(errorMsg || `HTTP ${response.status} — request failed`);
  }

  return response.json();
}

/**
 * Dedicated upload helper that POSTs a FormData payload to /api/docs/upload.
 * Returns the full extraction result including Gemini structured JSON.
 */
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  return apiFetch('/docs/upload', {
    method: 'POST',
    body: formData,
  });
}
