import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import Badge from "../components/Badge.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatCard from "../components/StatCard.jsx";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [profit, setProfit] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.dashboard(), api.weeklyProfit()])
      .then(([dashboardData, profitData]) => {
        setData(dashboardData);
        setProfit(profitData);
      })
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="card text-red-700">{error}</p>;
  if (!data) return <p className="card">Loading dashboard...</p>;

  const summary = data?.summary || {};
  const metrics = getMetrics(data);
  const actions = getActions(data.recommendations, data.actions);
  const weeklyRitual = getWeeklyRitual();
  const chartData = [
    { name: "Delivered", orders: metrics.delivered_orders },
    { name: "Cancelled", orders: metrics.cancelled_orders },
    { name: "RTO", orders: metrics.rto_orders },
    { name: "Unknown", orders: metrics.unknown_orders },
  ];

  async function markDone(id) {
    await api.markActionDone(id);
    setData(await api.dashboard());
  }

  return (
    <>
      <PageHeader title="Dashboard">What should I do today to increase profitable orders and reduce losses?</PageHeader>
      <section className="mb-5 rounded-3xl border border-emerald-200 bg-gradient-to-r from-emerald-50 via-white to-amber-50 p-4 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-black uppercase tracking-wide text-emerald-700">Weekly ritual</p>
            <h2 className="mt-1 text-lg font-black text-slate-900">Upload the week’s report every Sunday evening</h2>
            <p className="mt-1 text-sm text-slate-600">Then review three recommendations before planning restocks or ad spend.</p>
          </div>
          <div className="grid gap-2 text-sm text-slate-700 md:text-right">
            <p><span className="font-bold">Next review:</span> {weeklyRitual.nextReview}</p>
            <p><span className="font-bold">Focus:</span> {weeklyRitual.focus}</p>
          </div>
        </div>
      </section>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Total Orders" value={metrics.total_orders} />
        <StatCard label="Delivered" value={metrics.delivered_orders} />
        <StatCard label="Cancelled" value={metrics.cancelled_orders} />
        <StatCard label="RTO" value={metrics.rto_orders} />
        <StatCard label="Revenue Estimate" value={money(metrics.revenue_estimate)} />
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="card">
          <h2 className="text-xl font-black">Daily AI Business Summary</h2>
          <p className="mt-3 leading-7 text-slate-700">{formatSummary(summary, metrics)}</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <p><span className="font-bold">Top SKU:</span> {metrics.top_selling_sku || "No data"}</p>
            <p><span className="font-bold">Worst SKU:</span> {metrics.worst_performing_sku || "No data"}</p>
            <p><span className="font-bold">Ad Orders:</span> {metrics.ad_orders ?? 0}</p>
            <p><span className="font-bold">Natural Orders:</span> {metrics.natural_orders ?? 0}</p>
          </div>
        </div>
        <div className="grid gap-5">
          <div className="card">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-xl font-black">Weekly Profit Snapshot</h2>
              <Link to="/weekly-profit" className="text-sm font-semibold text-merchant hover:underline">
                Open full report
              </Link>
            </div>
            {profit?.summary ? (
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <p><span className="font-bold">Net Profit:</span> {money(profit.summary.net_profit)}</p>
                <p><span className="font-bold">Margin:</span> {profit.summary.profit_margin_percent}%</p>
                <p><span className="font-bold">Sales:</span> {money(profit.summary.sales)}</p>
                <p>
                  <span className="font-bold">Status:</span>{" "}
                  <Badge tone={profit.summary.net_profit >= 0 ? "safe" : "risk"}>{profit.summary.status}</Badge>
                </p>
              </div>
            ) : (
              <p className="mt-3 text-slate-500">Upload dated orders to calculate weekly profit or loss.</p>
            )}
          </div>

          <div className="card">
            <h2 className="text-xl font-black">Today’s 3 Actions</h2>
            <div className="mt-3 grid gap-3">
              {actions.map((action, index) =>
                typeof action === "object" && action?.id ? (
                  <label key={action.id} className="flex items-start gap-3 rounded-lg border border-slate-200 p-3">
                    <input type="checkbox" checked={Boolean(action.done)} onChange={() => markDone(action.id)} className="mt-1 h-5 w-5 accent-emerald-700" />
                    <span className={action.done ? "text-slate-400 line-through" : ""}>{action.text}</span>
                  </label>
                ) : (
                  <p key={`${index}-${action}`} className="rounded-lg border border-slate-200 p-3 text-slate-700">{action}</p>
                )
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="card mt-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-xl font-black">Order Status Mix</h2>
          <Badge tone={metrics.rto_orders > 0 ? "risk" : "safe"}>{metrics.rto_orders > 0 ? "Watch RTO" : "Low Risk"}</Badge>
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

function money(value) {
  return `₹${Math.round(value || 0).toLocaleString("en-IN")}`;
}

function getMetrics(data) {
  if (data?.metrics) {
    return {
      total_orders: data.metrics.total_orders ?? 0,
      delivered_orders: data.metrics.delivered_orders ?? 0,
      cancelled_orders: data.metrics.cancelled_orders ?? 0,
      rto_orders: data.metrics.rto_orders ?? 0,
      unknown_orders: data.metrics.unknown_orders ?? 0,
      revenue_estimate: data.metrics.revenue_estimate ?? 0,
      top_selling_sku: data.metrics.top_selling_sku ?? "",
      worst_performing_sku: data.metrics.worst_performing_sku ?? "",
      ad_orders: data.metrics.ad_orders ?? 0,
      natural_orders: data.metrics.natural_orders ?? 0,
    };
  }

  const summary = data?.summary && typeof data.summary === "object" ? data.summary : {};
  const totalOrders = summary.orders ?? 0;
  const deliveredOrders = Math.round(totalOrders * ((summary.delivered_rate ?? 0) / 100));
  const cancelledOrders = Math.round(totalOrders * ((summary.cancelled_rate ?? 0) / 100));
  const rtoOrders = Math.round(totalOrders * ((summary.rto_rate ?? 0) / 100));
  const unknownOrders = Math.max(0, totalOrders - deliveredOrders - cancelledOrders - rtoOrders);

  return {
    total_orders: totalOrders,
    delivered_orders: deliveredOrders,
    cancelled_orders: cancelledOrders,
    rto_orders: rtoOrders,
    unknown_orders: unknownOrders,
    revenue_estimate: summary.revenue ?? 0,
    top_selling_sku: data?.top_sku?.product_name || data?.top_sku?.sku || "",
    worst_performing_sku: "",
    ad_orders: data?.top_sku?.ad_orders ?? 0,
    natural_orders: data?.top_sku?.natural_orders ?? 0,
  };
}

function getActions(recommendations, existingActions) {
  if (Array.isArray(existingActions) && existingActions.length) {
    return existingActions;
  }

  const actions = [];
  const promote = recommendations?.promote_skus?.[0];
  const pause = recommendations?.pause_skus?.[0];
  const listing = recommendations?.listing_improvements?.[0];
  const safeCombo = recommendations?.safe_combos?.[0];

  if (promote) actions.push(`Promote ${promote.product_name || promote.sku} in ads.`);
  if (pause) actions.push(`Pause ${pause.product_name || pause.sku} until RTO and cancellation improve.`);
  if (listing) actions.push(`Rewrite ${listing.product_name || listing.sku} listing title and bullets.`);
  if (actions.length < 3 && safeCombo) {
    actions.push(`Scale ${safeCombo.sku} in ${safeCombo.customer_state} because delivery quality is strong.`);
  }
  while (actions.length < 3) {
    actions.push("Upload fresh orders tomorrow and review SKU scores before spending on ads.");
  }

  return actions.slice(0, 3);
}

function formatSummary(summary, metrics) {
  if (typeof summary === "string" && summary.trim()) {
    return summary;
  }

  if (summary && typeof summary === "object") {
    const parts = [];
    if (summary.orders != null) parts.push(`${summary.orders} orders across ${summary.skus ?? 0} SKUs`);
    if (summary.delivered_rate != null) parts.push(`${summary.delivered_rate}% delivered`);
    if (summary.rto_rate != null) parts.push(`${summary.rto_rate}% RTO`);
    if (summary.cancelled_rate != null) parts.push(`${summary.cancelled_rate}% cancelled`);
    if (summary.revenue != null) parts.push(`Revenue estimate ${money(summary.revenue)}`);
    if (parts.length) {
      return `${parts.join(". ")}.`;
    }
  }

  return `Track orders, returns, and revenue from today's uploaded data. Top SKU: ${metrics.top_selling_sku || "No data"}.`;
}

function getWeeklyRitual() {
  const today = new Date();
  const dayIndex = today.getDay();
  const daysUntilSunday = (7 - dayIndex) % 7 || 7;
  const nextSunday = new Date(today);
  nextSunday.setDate(today.getDate() + daysUntilSunday);
  const formatter = new Intl.DateTimeFormat("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "short",
  });

  return {
    nextReview: formatter.format(nextSunday),
    focus: "Three insights, one action list, one restock decision",
  };
}
