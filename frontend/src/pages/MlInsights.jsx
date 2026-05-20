import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import Badge from "../components/Badge.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatCard from "../components/StatCard.jsx";

export default function MlInsights() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.mlInsights().then(setData).catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="card text-red-700">{error}</p>;
  if (!data) return <p className="card">Preparing growth plan...</p>;

  const topForecast = data.demand_forecast?.[0];
  const topRisk = data.rto_predictions?.[0];
  const topOpportunity = data.profit_opportunities?.[0];

  return (
    <>
      <PageHeader title="Growth Planner">Plan stock, ads, and return-risk actions from your uploaded orders.</PageHeader>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Plan Status" value={data.engine?.sklearn_available ? "Ready" : "Basic"} />
        <StatCard label="Highest Demand" value={topForecast?.sku || "No data"} />
        <StatCard label="Highest Return Risk" value={topRisk ? `${topRisk.rto_probability}%` : "No data"} />
        <StatCard label="Best Growth SKU" value={topOpportunity?.sku || "No data"} />
      </section>

      <section className="card mt-5">
        <h2 className="text-xl font-black">Today’s Business Reading</h2>
        <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-3">
          <p className="rounded-lg bg-slate-50 p-3">Use the sales plan to decide how much stock to keep ready for the next 14 days.</p>
          <p className="rounded-lg bg-slate-50 p-3">Use return risk before spending more on ads in a state or SKU.</p>
          <p className="rounded-lg bg-slate-50 p-3">Use growth actions to decide what to scale, test, or fix first.</p>
        </div>
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-2">
        <DataTable
          title="Next 14 Days Sales Plan"
          emptyText="Upload dated orders to prepare a sales plan."
          items={data.demand_forecast || []}
          columns={[
            ["sku", "SKU"],
            ["forecast_units", "Expected Orders"],
            ["avg_daily_forecast", "Per Day"],
            ["trend", "Direction"],
            ["confidence", "Data Strength"]
          ]}
        />
        <DataTable
          title="Return Risk Watchlist"
          emptyText="Upload orders with state and delivery status to see return risk."
          items={data.rto_predictions || []}
          columns={[
            ["sku", "SKU"],
            ["customer_state", "State"],
            ["rto_probability", "Risk %"],
            ["risk_label", "Risk"],
            ["confidence", "Data Strength"]
          ]}
          badgeColumn="risk_label"
        />
      </section>

      <section className="card mt-5 overflow-x-auto">
        <h2 className="mb-3 text-xl font-black">What to Push, Test, or Fix</h2>
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500">
            <tr><th className="py-2">SKU</th><th>Expected Orders</th><th>Sales Value</th><th>Return Risk</th><th>Priority</th><th>Action</th></tr>
          </thead>
          <tbody>
            {(data.profit_opportunities || []).map((item) => (
              <tr key={item.sku} className="border-t border-slate-200">
                <td className="py-3 font-semibold">{item.sku}</td>
                <td>{item.forecast_units}</td>
                <td>₹{Math.round(item.revenue).toLocaleString("en-IN")}</td>
                <td>{item.rto_probability}%</td>
                <td>{item.opportunity_score}</td>
                <td><Badge tone={item.decision.includes("Scale") ? "safe" : item.decision.includes("Fix") ? "risk" : "neutral"}>{sellerDecision(item.decision)}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
        {!data.profit_opportunities?.length && <p className="py-6 text-sm text-slate-500">Upload delivered orders to prepare growth actions.</p>}
      </section>
    </>
  );
}

function DataTable({ title, items, columns, badgeColumn, emptyText }) {
  return (
    <div className="card overflow-x-auto">
      <h2 className="mb-3 text-xl font-black">{title}</h2>
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-slate-500">
          <tr>{columns.map(([, label]) => <th key={label} className="py-2">{label}</th>)}</tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr key={`${title}-${index}`} className="border-t border-slate-200">
              {columns.map(([key]) => (
                <td key={key} className={key === "sku" ? "py-3 font-semibold" : "py-3"}>
                  {key === badgeColumn ? <Badge tone={item[key] === "High Risk" ? "risk" : item[key] === "Low Risk" ? "safe" : "neutral"}>{item[key]}</Badge> : item[key] ?? "-"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {!items.length && <p className="py-6 text-sm text-slate-500">{emptyText}</p>}
    </div>
  );
}

function sellerDecision(decision) {
  if (decision === "Scale Ads and Stock") return "Push More";
  if (decision === "Fix RTO Before Scaling") return "Fix Returns First";
  if (decision === "Test Carefully") return "Test Slowly";
  return "Watch";
}
