const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }
  return response.json();
}

export const api = {
  uploadCsv(file) {
    const form = new FormData();
    form.append("file", file);
    return request("/api/upload", { method: "POST", body: form });
  },
  dashboard: () => request("/api/dashboard"),
  skuScores: () => request("/api/sku-scores"),
  rtoRisk: () => request("/api/rto-risk"),
  recommendations: () => request("/api/recommendations"),
  listingDoctor: (payload) => request("/api/listing-doctor", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }),
  inventory: () => request("/api/inventory"),
  saveInventory: (payload) => request("/api/inventory", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }),
  markActionDone: (id) => request(`/api/actions/${id}/done`, { method: "POST" }),
  usage: () => request("/api/usage"),
  mlInsights: () => request("/api/ml-insights"),
  ask: (question) => request("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question })
  })
};
