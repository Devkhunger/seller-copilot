import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";

export default function Usage() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.usage().then((res) => setItems(res.items)); }, []);
  return (
    <>
      <PageHeader title="Usage Tracking">Activity logs show uploads, dashboard views, checklist completion, listing generation, and inventory updates.</PageHeader>
      <div className="card overflow-x-auto">
        <table className="w-full min-w-[680px] text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="py-3">Time</th><th>Event</th><th>Detail</th></tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t border-slate-200">
                <td className="py-3">{item.created_at}</td>
                <td className="font-bold">{item.event_type.replaceAll("_", " ")}</td>
                <td>{item.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && <p className="py-8 text-center text-slate-500">No usage events yet.</p>}
      </div>
    </>
  );
}

