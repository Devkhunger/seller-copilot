import { useEffect, useState } from "react";
import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client.js";
import Badge from "../components/Badge.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatCard from "../components/StatCard.jsx";

const fields = [
  ["product_cost_percent", "Product cost %"],
  ["marketplace_fee_percent", "Marketplace fee %"],
  ["forward_shipping_per_order", "Shipping per order"],
  ["return_shipping_per_order", "Return shipping"],
  ["ad_cost_percent", "Ad cost %"]
];

export default function WeeklyProfit() {
  const [data, setData] = useState(null);
  const [settings, setSettings] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    const result = await api.weeklyProfit();
    setData(result);
    setSettings(result.settings || {});
  }

  useEffect(() => { load().catch((err) => setError(err.message)); }, []);

  async function saveSettings(event) {
    event.preventDefault();
    setSaving(true);
    await api.saveProfitSettings(settings);
    await load();
    setSaving(false);
  }

  if (error) return <p className="card text-red-700">{error}</p>;
  if (!data) return <p className="card">Preparing weekly profit...</p>;

  const summary = data.summary;
  const trendData = data.week_trend || [];
  const latestChange = data.latest_week_change;
  const latestTrend = trendData[trendData.length - 1] || null;
  const bestWeek = [...trendData].sort((a, b) => (b.net_profit || 0) - (a.net_profit || 0))[0] || null;
  const worstWeek = [...trendData].sort((a, b) => (a.net_profit || 0) - (b.net_profit || 0))[0] || null;
  const skuProfit = data.sku_profit || [];
  const profitDrivers = [...skuProfit].filter((item) => (item.net_profit || 0) > 0).slice(0, 3);
  const lossDrivers = [...skuProfit].filter((item) => (item.net_profit || 0) < 0).sort((a, b) => (a.net_profit || 0) - (b.net_profit || 0)).slice(0, 3);
  const money = (value) => `₹${Math.round(value || 0).toLocaleString("en-IN")}`;
  const signedMoney = (value) => {
    const amount = Math.round(value || 0).toLocaleString("en-IN");
    if (value > 0) return `+₹${amount}`;
    if (value < 0) return `-₹${Math.abs(Math.round(value || 0)).toLocaleString("en-IN")}`;
    return `₹0`;
  };

  return (
    <>
      <PageHeader title="Weekly Profit">Track whether the business is actually making money after returns, shipping, fees, ads, and product cost.</PageHeader>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Net Profit" value={money(summary.net_profit)} />
        <StatCard label="Sales" value={money(summary.sales)} />
        <StatCard label="Return Loss" value={money(summary.return_loss)} />
        <StatCard label="RTO Loss" value={money(summary.rto_loss)} />
        <StatCard label="Margin" value={`${summary.profit_margin_percent}%`} />
        <StatCard label="Status" value={summary.status} />
      </section>

      <section className="mt-5 grid gap-4 lg:grid-cols-3">
        <div className="card border border-slate-200 bg-gradient-to-br from-slate-50 to-white lg:col-span-2">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-xl font-black">Action Summary</h2>
            <Badge tone={latestChange?.trend === "Down" ? "risk" : latestChange?.trend === "Up" ? "safe" : "neutral"}>{latestChange?.trend || "No Trend"}</Badge>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <p className="text-xs uppercase tracking-wide text-slate-500">Latest shift</p>
              <p className={`mt-2 text-lg font-extrabold ${latestChange?.change_value < 0 ? "text-red-700" : "text-emerald-700"}`}>{latestChange?.change_value == null ? "No prior week" : signedMoney(latestChange.change_value)}</p>
              <p className="mt-1 text-sm text-slate-600">Compared with the previous week.</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <p className="text-xs uppercase tracking-wide text-slate-500">Best week</p>
              <p className="mt-2 text-lg font-extrabold text-slate-900">{bestWeek?.week_start || "-"}</p>
              <p className="mt-1 text-sm text-slate-600">{bestWeek ? money(bestWeek.net_profit) : "No trend data yet."}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <p className="text-xs uppercase tracking-wide text-slate-500">Worst week</p>
              <p className="mt-2 text-lg font-extrabold text-slate-900">{worstWeek?.week_start || "-"}</p>
              <p className="mt-1 text-sm text-slate-600">{worstWeek ? money(worstWeek.net_profit) : "No trend data yet."}</p>
            </div>
          </div>
          <div className="mt-4 grid gap-2 text-sm text-slate-600">
            {latestChange?.trend === "Down" && (
              <p className="rounded-lg bg-red-50 p-3 text-red-800">Profit fell this week. Check returns, RTO, and ad spend before scaling further.</p>
            )}
            {latestChange?.trend === "Up" && (
              <p className="rounded-lg bg-emerald-50 p-3 text-emerald-800">Profit improved this week. Keep the winning SKUs and watch whether the uplift continues next week.</p>
            )}
            {latestChange?.trend === "Flat" && (
              <p className="rounded-lg bg-amber-50 p-3 text-amber-900">Profit stayed flat. Small pricing or return changes could unlock the next jump.</p>
            )}
            {!latestChange && (
              <p className="rounded-lg bg-slate-50 p-3 text-slate-600">Upload a few dated weeks to unlock a useful trend summary.</p>
            )}
          </div>
        </div>
        <div className="card border border-slate-200">
          <h3 className="text-lg font-black">What to do next</h3>
          <ul className="mt-3 space-y-3 text-sm text-slate-700">
            <li className="rounded-lg bg-slate-50 p-3">Keep an eye on the latest week trend: {latestTrend ? `${latestTrend.trend} (${latestTrend.week_start})` : "not enough data yet"}.</li>
            <li className="rounded-lg bg-slate-50 p-3">If profit is down, first check return loss and RTO loss before changing product costs.</li>
            <li className="rounded-lg bg-slate-50 p-3">If profit is up, keep the same winning SKU mix and compare next week with this baseline.</li>
          </ul>
        </div>
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[1fr_1fr]">
        <div className="card">
          <h2 className="mb-4 text-xl font-black">Top Profit Drivers</h2>
          {profitDrivers.length ? (
            <ul className="space-y-3 text-sm">
              {profitDrivers.map((item, index) => (
                <li key={`${item.sku}-profit`} className="rounded-lg border border-emerald-100 bg-emerald-50/70 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-bold text-slate-900">#{index + 1} {item.product_name || item.sku}</p>
                      <p className="text-slate-600">Sales {money(item.sales)} · Return loss {money(item.return_loss)} · RTO loss {money(item.rto_loss)}</p>
                    </div>
                    <Badge tone="safe">{money(item.net_profit)}</Badge>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">Upload more delivered orders to see top profit drivers.</p>
          )}
        </div>
        <div className="card">
          <h2 className="mb-4 text-xl font-black">Top Loss Drivers</h2>
          {lossDrivers.length ? (
            <ul className="space-y-3 text-sm">
              {lossDrivers.map((item, index) => (
                <li key={`${item.sku}-loss`} className="rounded-lg border border-red-100 bg-red-50/70 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-bold text-slate-900">#{index + 1} {item.product_name || item.sku}</p>
                      <p className="text-slate-600">Sales {money(item.sales)} · Return loss {money(item.return_loss)} · RTO loss {money(item.rto_loss)}</p>
                    </div>
                    <Badge tone="risk">{money(item.net_profit)}</Badge>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">Upload more weeks to surface the weakest SKUs.</p>
          )}
        </div>
      </section>

      <section className="mt-5">
        <div className="card">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-xl font-black">Week-over-Week Change</h2>
            <Badge tone={latestChange?.trend === "Down" ? "risk" : "safe"}>{latestChange?.trend || "No Trend"}</Badge>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <StatCard label="Latest Change" value={signedMoney(latestChange?.change_value)} />
            <StatCard label="Change %" value={latestChange?.change_percent == null ? "-" : `${latestChange.change_percent}%`} />
            <StatCard label="Latest Week" value={latestChange?.week_start || "-"} />
          </div>
          <p className="mt-4 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">Positive values mean profit improved versus the previous week. Negative values mean profit dropped.</p>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="week_start" tickLine={false} axisLine={false} />
                <YAxis tickFormatter={(value) => `₹${Math.round(value / 1000)}k`} />
                <Tooltip formatter={(value, name) => [money(value), name === "net_profit" ? "Net Profit" : "Change"]} />
                <Bar dataKey="net_profit" fill="#1d4ed8" radius={[6, 6, 0, 0]} />
                <Line type="monotone" dataKey="change_value" stroke="#f97316" strokeWidth={3} dot={{ r: 3 }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <form onSubmit={saveSettings} className="card">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-xl font-black">Cost Settings</h2>
            <Badge tone={summary.net_profit >= 0 ? "safe" : "risk"}>{summary.status}</Badge>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {fields.map(([key, label]) => (
              <label key={key} className="label">
                {label}
                <input
                  className="input"
                  type="number"
                  min="0"
                  step="0.1"
                  value={settings[key] ?? 0}
                  onChange={(event) => setSettings({ ...settings, [key]: Number(event.target.value) })}
                />
              </label>
            ))}
          </div>
          <button className="btn mt-4" disabled={saving}>{saving ? "Saving..." : "Save Costs"}</button>
          <div className="mt-4 grid gap-2 text-sm text-slate-600">
            {(data.explanation || []).map((item) => <p key={item} className="rounded-lg bg-slate-50 p-3">{item}</p>)}
          </div>
        </form>

        <section className="card overflow-x-auto">
          <h2 className="mb-3 text-xl font-black">Weekly Profit/Loss</h2>
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr><th className="py-2">Week</th><th>Sales</th><th>Profit</th><th>Return Loss</th><th>RTO Loss</th><th>Net</th><th>Status</th></tr>
            </thead>
            <tbody>
              {(data.weeks || []).map((week) => (
                <tr key={week.week_start} className="border-t border-slate-200">
                  <td className="py-3 font-semibold">{week.week_start}</td>
                  <td>{money(week.sales)}</td>
                  <td>{money(week.delivered_profit)}</td>
                  <td>{money(week.return_loss)}</td>
                  <td>{money(week.rto_loss)}</td>
                  <td className={week.net_profit < 0 ? "font-bold text-red-700" : "font-bold text-emerald-700"}>{money(week.net_profit)}</td>
                  <td><Badge tone={week.net_profit >= 0 ? "safe" : "risk"}>{week.status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data.weeks?.length && <p className="py-6 text-sm text-slate-500">Upload dated orders to see weekly profit.</p>}
        </section>
      </section>

      <section className="card mt-5 overflow-x-auto">
        <h2 className="mb-3 text-xl font-black">SKU Profit Ranking</h2>
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500">
            <tr><th className="py-2">SKU</th><th>Sales</th><th>Return Loss</th><th>RTO Loss</th><th>Net</th><th>Returned</th><th>RTO</th><th>Status</th></tr>
          </thead>
          <tbody>
            {(data.sku_profit || []).map((item) => (
              <tr key={item.sku} className="border-t border-slate-200">
                <td className="py-3 font-semibold">{item.sku}<span className="block text-xs font-normal text-slate-500">{item.product_name}</span></td>
                <td>{money(item.sales)}</td>
                <td>{money(item.return_loss)}</td>
                <td>{money(item.rto_loss)}</td>
                <td className={item.net_profit < 0 ? "font-bold text-red-700" : "font-bold text-emerald-700"}>{money(item.net_profit)}</td>
                <td>{item.returned_orders}</td>
                <td>{item.rto_orders}</td>
                <td><Badge tone={item.net_profit >= 0 ? "safe" : "risk"}>{item.status}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
