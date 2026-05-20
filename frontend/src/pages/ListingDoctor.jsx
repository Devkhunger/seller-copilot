import { useState } from "react";
import { api } from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";

const initial = {
  product_name: "",
  fabric: "",
  color: "",
  size: "",
  design: "",
  platform: "Meesho"
};

export default function ListingDoctor() {
  const [form, setForm] = useState(initial);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    try {
      setResult(await api.listingDoctor(form));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader title="AI Listing Doctor">Generate marketplace-ready title, bullets, description, keywords, and platform text.</PageHeader>
      <section className="grid gap-5 xl:grid-cols-[360px_1fr]">
        <form onSubmit={submit} className="card grid gap-4">
          <label className="label">Product name<input required className="input" value={form.product_name} onChange={(e) => update("product_name", e.target.value)} placeholder="Cushion Cover" /></label>
          <label className="label">Fabric<input className="input" value={form.fabric} onChange={(e) => update("fabric", e.target.value)} placeholder="Velvet" /></label>
          <label className="label">Color<input className="input" value={form.color} onChange={(e) => update("color", e.target.value)} placeholder="Sea Green" /></label>
          <label className="label">Size<input className="input" value={form.size} onChange={(e) => update("size", e.target.value)} placeholder="16x16 Inch" /></label>
          <label className="label">Print / Design<input className="input" value={form.design} onChange={(e) => update("design", e.target.value)} placeholder="Zipper Closure" /></label>
          <label className="label">Platform
            <select className="input" value={form.platform} onChange={(e) => update("platform", e.target.value)}>
              <option>Meesho</option>
              <option>Flipkart</option>
              <option>Amazon</option>
            </select>
          </label>
          <button className="btn" disabled={loading}>{loading ? "Generating..." : "Generate Listing"}</button>
        </form>
        <div className="card">
          {!result && <p className="text-slate-500">Listing output will appear here.</p>}
          {result && (
            <div className="grid gap-4">
              <Block title="SEO Title">{result.seo_title}</Block>
              <Block title="Short Description">{result.short_description}</Block>
              <Block title="Bullet Points">
                <ul className="list-disc space-y-1 pl-5">{result.bullet_points.map((point) => <li key={point}>{point}</li>)}</ul>
              </Block>
              <Block title="Keywords">{result.keywords.join(", ")}</Block>
              <Block title="Platform Text">{result.platform_text}</Block>
            </div>
          )}
        </div>
      </section>
    </>
  );
}

function Block({ title, children }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <h2 className="mb-2 font-black">{title}</h2>
      <div className="text-slate-700">{children}</div>
    </div>
  );
}

