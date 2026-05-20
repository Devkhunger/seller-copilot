import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [name, setName] = useState(localStorage.getItem("sellerName") || "");

  function submit(event) {
    event.preventDefault();
    localStorage.setItem("sellerName", name || "Demo Seller");
    navigate("/upload");
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 p-5">
      <form onSubmit={submit} className="card w-full max-w-md">
        <p className="text-xs font-black uppercase tracking-wide text-merchant">AI Seller Copilot</p>
        <h1 className="mt-2 text-3xl font-black">Daily decisions for ecommerce sellers</h1>
        <p className="mt-2 text-slate-600">Enter a seller name to start. No password needed for this MVP.</p>
        <label className="label mt-6">
          Seller name
          <input className="input" value={name} onChange={(event) => setName(event.target.value)} placeholder="Riya Home Decor" />
        </label>
        <button className="btn mt-5 w-full">Continue</button>
      </form>
    </main>
  );
}

