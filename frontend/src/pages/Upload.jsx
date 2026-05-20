import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      setResult(await api.uploadCsv(file));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader title="Upload Order CSV">Upload Meesho, Flipkart, or Amazon order reports. Messy column names are mapped automatically.</PageHeader>
      <form onSubmit={submit} className="card max-w-3xl">
        <label className="label">
          Order report CSV
          <input className="input" type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0])} />
        </label>
        <div className="mt-4 flex flex-wrap gap-3">
          <button className="btn" disabled={!file || loading}>{loading ? "Uploading..." : "Clean and Analyze"}</button>
          <a className="btn-soft" href="/sample_data/sample_orders.csv">Download Sample CSV</a>
        </div>
        {error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm font-semibold text-red-700">{error}</p>}
        {result && (
          <div className="mt-4 rounded-lg bg-emerald-50 p-4 text-emerald-900">
            <p className="font-bold">Imported {result.rows_imported} rows.</p>
            {result.warnings?.length > 0 && <p className="mt-1 text-sm">Warnings: {result.warnings.join(", ")}</p>}
            <Link className="mt-3 inline-block font-bold underline" to="/dashboard">Open dashboard</Link>
          </div>
        )}
      </form>
    </>
  );
}

