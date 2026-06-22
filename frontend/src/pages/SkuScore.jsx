import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import Badge from "../components/Badge.jsx";
import PageHeader from "../components/PageHeader.jsx";

export default function SkuScore() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.skuScores().then((res) => setItems(res.items)); }, []);
  return (
    <>
      <PageHeader title="SKU Score">Score now uses delivered rate, order volume, RTO, cancellation, ad mix, discount pressure, freshness, and momentum.</PageHeader>
      <div className="card overflow-x-auto">
        <table className="w-full min-w-[1220px] text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="py-3">SKU</th><th>Orders</th><th>Delivered %</th><th>Cancelled %</th><th>RTO %</th><th>Natural %</th><th>Ad %</th><th>Discount %</th><th>Freshness</th><th>Momentum</th><th>Consistency</th><th>Score</th><th>Action</th></tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.sku} className="border-t border-slate-200">
                <td className="py-3 font-semibold">{item.product_name}<span className="block text-xs text-slate-500">{item.sku}</span></td>
                <td>{item.orders}</td>
                <td>{item.delivered_rate}%</td>
                <td>{item.cancelled_rate}%</td>
                <td>{item.rto_rate}%</td>
                <td>{item.natural_share_pct}%</td>
                <td>{item.ad_share_pct}%</td>
                <td>{item.avg_discount_pct}%</td>
                <td>{item.recency_score}</td>
                <td>{item.momentum_score}</td>
                <td>{item.consistency_score}</td>
                <td className="font-black">{item.score}</td>
                <td><Badge>{item.action}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && <p className="py-8 text-center text-slate-500">Upload a CSV to see SKU scores.</p>}
      </div>
    </>
  );
}

