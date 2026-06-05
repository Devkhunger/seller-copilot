import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import Badge from "../components/Badge.jsx";
import PageHeader from "../components/PageHeader.jsx";

export default function RtoRisk() {
  const [risk, setRisk] = useState(null);
  const [recs, setRecs] = useState(null);
  useEffect(() => {
    api.rtoRisk().then(setRisk);
    api.recommendations().then(setRecs);
  }, []);
  if (!risk) return <p className="card">Loading RTO risk...</p>;
  return (
    <>
      <PageHeader title="Return Risk Shield">Shows risky states and products where returns are high. High risk means return rate is at least 20% with minimum 5 orders.</PageHeader>
      <section className="grid gap-5 xl:grid-cols-3">
        <RiskTable title="High-Risk States" items={risk.high_risk_states} columns={["customer_state"]} />
        <RiskTable title="High-Risk SKUs" items={risk.high_risk_skus} columns={["sku"]} />
        <RiskTable title="State + SKU Risk" items={risk.high_risk_combos} columns={["customer_state", "sku"]} />
      </section>
      <section className="mt-5 grid gap-5 xl:grid-cols-[1fr_360px]">
        <div className="card">
          <h2 className="text-xl font-black">Promotion Insights</h2>
          <div className="mt-3 grid gap-2">
            {(recs?.insights || []).map((insight) => <p key={insight} className="rounded-lg bg-slate-50 p-3">{insight}</p>)}
            {!recs?.insights?.length && <p className="text-slate-500">No high-risk insight yet. Upload more orders for better signals.</p>}
          </div>
        </div>

        <aside className="card">
          <h2 className="text-xl font-black">Run Ads On</h2>
          {recs?.ad_recommendation ? (
            <div className="mt-3 grid gap-3">
              <p className="rounded-lg bg-emerald-50 p-3 text-emerald-900">
                Promote <span className="font-bold">{recs.ad_recommendation.product_name}</span> ({recs.ad_recommendation.sku})
              </p>
              <p className="text-sm leading-6 text-slate-700">Target: <span className="font-semibold">{recs.ad_recommendation.recommended_state}</span></p>
              <p className="text-sm leading-6 text-slate-700">Why: {recs.ad_recommendation.reason}</p>
              <p className="text-sm leading-6 text-slate-700">Confidence: {recs.ad_recommendation.confidence}</p>
            </div>
          ) : (
            <p className="mt-3 text-slate-500">Upload more orders so we can pick a SKU to promote with ads.</p>
          )}
        </aside>
      </section>
    </>
  );
}

function RiskTable({ title, items, columns }) {
  return (
    <div className="card overflow-x-auto">
      <h2 className="mb-3 text-lg font-black">{title}</h2>
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-slate-500">
          <tr><th className="py-2">Segment</th><th>Orders</th><th>RTO</th><th>Risk</th></tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr key={index} className="border-t border-slate-200">
              <td className="py-3 font-semibold">{columns.map((col) => item[col]).join(" / ")}</td>
              <td>{item.orders}</td>
              <td>{item.rto_rate}%</td>
              <td><Badge tone={item.risk_label === "High Risk" ? "risk" : "safe"}>{item.risk_label}</Badge></td>
            </tr>
          ))}
        </tbody>
      </table>
      {!items.length && <p className="py-6 text-sm text-slate-500">No high-risk rows found.</p>}
    </div>
  );
}

