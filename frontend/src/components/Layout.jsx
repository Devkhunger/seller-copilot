import { useEffect, useState } from "react";
import { NavLink, Outlet, Navigate, useNavigate } from "react-router-dom";
import { api, clearSession } from "../api/client.js";
import LanguageToggle from "./LanguageToggle.jsx";

const links = [
  ["/upload", "Upload", "↑"],
  ["/dashboard", "Dashboard", "⌂"],
  ["/sku-score", "SKU Score", "◆"],
  ["/rto-risk", "Return Risk", "!"],
  ["/ask", "Ask Copilot", "✦"],
  ["/listing-doctor", "Listing Doctor", "✎"],
  ["/inventory", "Inventory", "▦"],
  ["/weekly-profit", "Weekly Profit", "₹"],
  ["/ml-insights", "Growth Planner", "↗"],
  ["/usage", "Usage", "◷"],
];

export default function Layout() {
  const navigate = useNavigate();
  const [token, setToken] = useState(() => localStorage.getItem("sellerToken"));
  const seller = localStorage.getItem("sellerName") || localStorage.getItem("sellerEmail") || "Seller";

  useEffect(() => {
    function syncAuth() {
      setToken(localStorage.getItem("sellerToken"));
    }

    window.addEventListener("seller-auth-changed", syncAuth);
    window.addEventListener("storage", syncAuth);
    return () => {
      window.removeEventListener("seller-auth-changed", syncAuth);
      window.removeEventListener("storage", syncAuth);
    };
  }, []);

  if (!token) return <Navigate to="/" replace />;

  async function logout() {
    try {
      await api.logout();
    } finally {
      clearSession();
      navigate("/", { replace: true });
    }
  }

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[268px_1fr]">
      <aside className="sidebar-shell flex flex-col bg-slate-950 p-4 text-white lg:sticky lg:top-0 lg:h-screen lg:p-5">
        <button onClick={() => navigate("/dashboard")} className="mb-6 flex w-full items-center gap-3 rounded-2xl p-2 text-left transition hover:bg-white/5">
          <span className="brand-mark grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-emerald-300 font-black text-slate-950">AI</span>
          <span className="min-w-0">
            <span className="block truncate text-lg font-black tracking-tight">Seller Copilot</span>
            <span className="mt-0.5 block truncate text-xs text-slate-400">{seller}</span>
          </span>
        </button>
        <div className="mb-4 flex items-center gap-2 rounded-xl border border-emerald-400/20 bg-emerald-400/10 px-3 py-2 text-xs font-semibold text-emerald-200">
          <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-300" />
          Business workspace active
        </div>
        <nav className="nav-scroll flex gap-1 overflow-x-auto pb-1 lg:grid lg:gap-1.5 lg:overflow-visible">
          {links.map(([to, label, icon]) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `nav-item flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition ${isActive ? "bg-white text-slate-950 shadow-lg shadow-black/10" : "text-slate-400 hover:bg-white/10 hover:text-white"}`}
            >
              <span className="grid h-6 w-6 place-items-center rounded-lg bg-white/10 text-xs font-black">{icon}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="mt-5 flex items-center gap-2 border-t border-white/10 pt-4 lg:mt-auto">
          <LanguageToggle dark />
          <button onClick={logout} className="btn-soft flex-1 bg-white/10 text-sm text-white hover:bg-white/15">Logout</button>
        </div>
      </aside>
      <main className="app-main min-w-0 p-4 sm:p-5 lg:p-8">
        <Outlet />
      </main>
    </div>
  );
}
