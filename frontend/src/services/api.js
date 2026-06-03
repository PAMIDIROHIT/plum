const BASE_URL = 'http://localhost:8000/api';

/**
 * Clean HTTP client fetch wrapper pointing to the backend API port.
 */
export async function apiFetch(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  
  const config = {
    ...options,
    headers
  };
  
  const response = await fetch(url, config);
  if (!response.ok) {
    const errorMsg = await response.text();
    throw new Error(errorMsg || `HTTP request failed with status ${response.status}`);
  }
  
  return response.json();
}
