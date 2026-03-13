const rawBase = process.env.REACT_APP_BACKEND_URL;

if (!rawBase && typeof window !== "undefined") {
  // Keep the app functional in misconfigured environments.
  console.warn("REACT_APP_BACKEND_URL is not set. Falling back to current origin.");
}

export const API_BASE = (rawBase || (typeof window !== "undefined" ? window.location.origin : "http://localhost:8001")).replace(/\/$/, "");
export const API = `${API_BASE}/api`;
