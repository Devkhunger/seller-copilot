import { useEffect, useState } from "react";
import { NavLink, Outlet, Navigate, useNavigate } from "react-router-dom";
import { api, clearSession } from "../api/client.js";

const links = [
  ["/upload", "Upload"],
  ["/dashboard", "Dashboard"],
  ["/sku-score", "SKU Score"],
  ["/rto-risk", "Return Risk"],
  ["/ask", "Ask Copilot"],
  ["/listing-doctor", "Listing Doctor"],
  ["/inventory", "Inventory"],
  ["/weekly-profit", "Weekly Profit"],
  ["/ml-insights", "Growth Planner"],
  ["/usage", "Usage"]
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

  if (!token) {
    return <Navigate to="/" replace />;
  }

  async function logout() {
    try {
      await api.logout();
    } finally {
      clearSession();
      navigate("/", { replace: true });
    }
  }

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="bg-slate-900 p-5 text-white lg:min-h-screen">
        <button onClick={() => navigate("/dashboard")} className="mb-7 flex items-center gap-3 text-left">
          <span className="grid h-10 w-10 place-items-center rounded-lg bg-emerald-300 font-black text-slate-900">AI</span>
          <span>
            <span className="block text-lg font-black">Seller Copilot</span>
            <span className="text-sm text-slate-300">{seller}</span>
          </span>
        </button>
        <nav className="grid gap-2">
          {links.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `rounded-lg px-3 py-2 font-semibold ${isActive ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5"}`}
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <button onClick={logout} className="btn-soft mt-6 w-full bg-white/10 text-white hover:bg-white/15">
          Logout
        </button>
      </aside>
      <main className="p-5 lg:p-8">
        <Outlet />
      </main>
    </div>
  );
}
