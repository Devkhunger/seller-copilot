import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import Badge from "../components/Badge.jsx";
import PageHeader from "../components/PageHeader.jsx";

export default function Inventory() {
  const [items, setItems] = useState([]);
  const [saving, setSaving] = useState("");

  async function load() {
    const result = await api.inventory();
    setItems(result.items);
  }

  useEffect(() => { load(); }, []);

  async function save(item, stock) {
    setSaving(item.sku);
    await api.saveInventory({ sku: item.sku, current_stock: Number(stock) || 0 });
    await load();
    setSaving("");
  }

  return (
    <>
      <PageHeader title="Inventory Alert">Predict stockout days using current stock divided by average daily orders.</PageHeader>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => <InventoryCard key={item.sku} item={item} onSave={save} saving={saving === item.sku} />)}
      </div>
      {!items.length && <p className="card text-slate-500">Upload a CSV first. SKUs will appear here.</p>}
    </>
  );
}

function InventoryCard({ item, onSave, saving }) {
  const [stock, setStock] = useState(item.current_stock);
  const tone = item.alert === "Stockout Risk" ? "risk" : item.alert === "Healthy" ? "safe" : "neutral";
  return (
    <article className="card">
      <div className="flex items-start justify-between gap-3">
        <h2 className="font-black">{item.sku}</h2>
        <Badge tone={tone}>{item.alert}</Badge>
      </div>
      <div className="mt-4 grid gap-3">
        <label className="label">Current stock<input className="input" type="number" min="0" value={stock} onChange={(event) => setStock(event.target.value)} /></label>
        <p className="text-sm text-slate-600">Avg daily orders: <span className="font-bold">{item.avg_daily_orders}</span></p>
        <p className="text-sm text-slate-600">Days left: <span className="font-bold">{item.days_left ?? "No sales yet"}</span></p>
        <button className="btn" onClick={() => onSave(item, stock)} disabled={saving}>{saving ? "Saving..." : "Save Stock"}</button>
      </div>
    </article>
  );
}

