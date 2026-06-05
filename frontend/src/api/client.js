
const API_BASE =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : import.meta.env.VITE_API_BASE || "http://localhost:8000";

function getToken() {
  return localStorage.getItem("sellerToken");
}

function emitAuthChange() {
  window.dispatchEvent(new Event("seller-auth-changed"));
}

function setSession(session) {
  localStorage.setItem("sellerToken", session.token);
  localStorage.setItem("sellerEmail", session.user.email);
  localStorage.setItem("sellerName", session.user.full_name || session.user.email);
  emitAuthChange();
}

export function clearSession() {
  localStorage.removeItem("sellerToken");
  localStorage.removeItem("sellerEmail");
  localStorage.removeItem("sellerName");
  emitAuthChange();
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getToken();
  if (token) {
    headers.set("X-Session-Token", token);
  }
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new Error(`Cannot reach the backend at ${API_BASE}. Make sure it is running.`);
  }
  if (response.status === 401) {
    const error = await response.json().catch(() => ({ detail: "Your session expired. Please sign in again." }));
    throw new Error(formatError(error));
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(formatError(error));
  }
  return response.json();
}

function formatError(error) {
  const detail = error?.detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = Array.isArray(item?.loc) ? item.loc.slice(1).join(".") : "field";
        const message = item?.msg || "Invalid value";
        return field ? `${field}: ${message}` : message;
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") {
    return detail.message || detail.error || JSON.stringify(detail);
  }
  if (typeof error === "string") {
    return error;
  }
  return "Request failed";
}

export const api = {
  register(payload) {
    return request("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((session) => {
      setSession(session);
      return session;
    });
  },
  login(payload) {
    return request("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((session) => {
      setSession(session);
      return session;
    });
  },
  logout() {
    return request("/api/auth/logout", { method: "POST" }).finally(() => clearSession());
  },
  me() {
    return request("/api/auth/me");
  },
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
    body: JSON.stringify(payload),
  }),
  inventory: () => request("/api/inventory"),
  saveInventory: (payload) => request("/api/inventory", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }),
  markActionDone: (id) => request(`/api/actions/${id}/done`, { method: "POST" }),
  usage: () => request("/api/usage"),
  mlInsights: () => request("/api/ml-insights"),
  weeklyProfit: () => request("/api/weekly-profit"),
  saveProfitSettings: (payload) => request("/api/profit-settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }),
  ask: (question) => request("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  }),
};
