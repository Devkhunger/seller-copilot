import { NavLink, Outlet, useNavigate } from "react-router-dom";

const links = [
  ["/upload", "Upload"],
  ["/dashboard", "Dashboard"],
  ["/sku-score", "SKU Score"],
  ["/rto-risk", "Return Risk"],
  ["/ask", "Ask Copilot"],
  ["/listing-doctor", "Listing Doctor"],
  ["/inventory", "Inventory"],
  ["/ml-insights", "Growth Planner"],
  ["/usage", "Usage"]
];

export default function Layout() {
  const navigate = useNavigate();
  const seller = localStorage.getItem("sellerName") || "Seller";
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
      </aside>
      <main className="p-5 lg:p-8">
        <Outlet />
      </main>
    </div>
  );
}
