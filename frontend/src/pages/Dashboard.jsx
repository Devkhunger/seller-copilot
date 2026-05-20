import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client.js";
import Badge from "../components/Badge.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatCard from "../components/StatCard.jsx";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.dashboard().then(setData).catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="card text-red-700">{error}</p>;
  if (!data) return <p className="card">Loading dashboard...</p>;
  const m = data.metrics;
  const chartData = [
    { name: "Delivered", orders: m.delivered_orders },
    { name: "Cancelled", orders: m.cancelled_orders },
    { name: "RTO", orders: m.rto_orders },
    { name: "Unknown", orders: m.unknown_orders }
  ];

  async function markDone(id) {
    await api.markActionDone(id);
    setData(await api.dashboard());
  }

  return (
    <>
      <PageHeader title="Dashboard">What should I do today to increase profitable orders and reduce losses?</PageHeader>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Total Orders" value={m.total_orders} />
        <StatCard label="Delivered" value={m.delivered_orders} />
        <StatCard label="Cancelled" value={m.cancelled_orders} />
        <StatCard label="RTO" value={m.rto_orders} />
        <StatCard label="Revenue Estimate" value={`₹${Math.round(m.revenue_estimate).toLocaleString("en-IN")}`} />
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="card">
          <h2 className="text-xl font-black">Daily AI Business Summary</h2>
          <p className="mt-3 leading-7 text-slate-700">{data.summary}</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <p><span className="font-bold">Top SKU:</span> {m.top_selling_sku || "No data"}</p>
            <p><span className="font-bold">Worst SKU:</span> {m.worst_performing_sku || "No data"}</p>
            <p><span className="font-bold">Ad Orders:</span> {m.ad_orders}</p>
            <p><span className="font-bold">Natural Orders:</span> {m.natural_orders}</p>
          </div>
        </div>
        <div className="card">
          <h2 className="text-xl font-black">Today’s 3 Actions</h2>
          <div className="mt-3 grid gap-3">
            {data.actions.map((action) => (
              <label key={action.id} className="flex items-start gap-3 rounded-lg border border-slate-200 p-3">
                <input type="checkbox" checked={Boolean(action.done)} onChange={() => markDone(action.id)} className="mt-1 h-5 w-5 accent-emerald-700" />
                <span className={action.done ? "text-slate-400 line-through" : ""}>{action.text}</span>
              </label>
            ))}
          </div>
        </div>
      </section>

      <section className="card mt-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-xl font-black">Order Status Mix</h2>
          <Badge tone={m.rto_orders > 0 ? "risk" : "safe"}>{m.rto_orders > 0 ? "Watch RTO" : "Low Risk"}</Badge>
        </div>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="orders" fill="#146C63" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </>
  );
}

