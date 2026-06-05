
import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api, clearSession } from "../api/client.js";

export default function Login() {

function formatLoginError(error) {
  const message = error?.message;
  if (typeof message === "string" && message.trim()) return message;
  const detail = error?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = Array.isArray(item?.loc) ? item.loc.slice(1).join(".") : "field";
        const msg = item?.msg || "Invalid value";
        return field ? `${field}: ${msg}` : msg;
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") {
    return detail.message || detail.error || JSON.stringify(detail);
  }
  if (typeof error === "string") return error;
  if (error && typeof error === "object") {
    return error.detail || error.error || error.message || JSON.stringify(error);
  }
  return "Login failed";
}
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    email: localStorage.getItem("sellerEmail") || "",
    password: "",
    full_name: localStorage.getItem("sellerName") || "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const token = localStorage.getItem("sellerToken");

  useEffect(() => {
    if (token) {
      navigate("/dashboard", { replace: true });
    }
  }, [navigate, token]);

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = {
        email: form.email,
        password: form.password,
        full_name: form.full_name,
      };
      if (mode === "register") {
        await api.register(payload);
      } else {
        await api.login(payload);
      }
      navigate("/dashboard", { replace: true });
    } catch (err) {
      clearSession();
      setError(formatLoginError(err));
    } finally {
      setLoading(false);
    }
  }

  if (token) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 p-5">
      <form onSubmit={submit} className="card w-full max-w-md">
        <p className="text-xs font-black uppercase tracking-wide text-merchant">AI Seller Copilot</p>
        <h1 className="mt-2 text-3xl font-black">Daily decisions for ecommerce sellers</h1>
        <p className="mt-2 text-slate-600">Sign in with your email so your orders, inventory, and insights stay separate from every other seller.</p>
        <div className="mt-6 flex gap-2 rounded-lg bg-slate-100 p-1 text-sm font-semibold">
          <button type="button" onClick={() => setMode("login")} className={`flex-1 rounded-md px-3 py-2 ${mode === "login" ? "bg-white text-slate-900 shadow" : "text-slate-500"}`}>
            Login
          </button>
          <button type="button" onClick={() => setMode("register")} className={`flex-1 rounded-md px-3 py-2 ${mode === "register" ? "bg-white text-slate-900 shadow" : "text-slate-500"}`}>
            Create account
          </button>
        </div>
        <label className="label mt-5">
          Email address
          <input className="input" type="email" value={form.email} onChange={(event) => update("email", event.target.value)} placeholder="seller@example.com" required />
        </label>
        {mode === "register" && (
          <label className="label mt-4">
            Seller name
            <input className="input" value={form.full_name} onChange={(event) => update("full_name", event.target.value)} placeholder="Riya Home Decor" />
          </label>
        )}
        <label className="label mt-4">
          Password
          <input className="input" type="password" minLength={8} value={form.password} onChange={(event) => update("password", event.target.value)} placeholder="Choose a strong password" required />
          <span className="mt-1 text-xs text-slate-500">Use at least 8 characters.</span>
        </label>
        {error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm font-semibold text-red-700">{typeof error === "string" ? error : formatLoginError(error)}</p>}
        <button className="btn mt-5 w-full" disabled={loading}>{loading ? "Please wait..." : mode === "register" ? "Create account" : "Sign in"}</button>
      </form>
    </main>
  );
}
