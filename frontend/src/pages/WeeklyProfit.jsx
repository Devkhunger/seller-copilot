import { useEffect, useState } from "react";
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
  const money = (value) => `₹${Math.round(value || 0).toLocaleString("en-IN")}`;

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
