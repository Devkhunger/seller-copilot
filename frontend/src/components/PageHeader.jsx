export default function PageHeader({ eyebrow = "AI Seller Copilot", title, children }) {
  return (
    <header className="mb-6">
      <p className="text-xs font-black uppercase tracking-wide text-merchant">{eyebrow}</p>
      <h1 className="mt-1 text-3xl font-black tracking-tight text-ink">{title}</h1>
      {children && <p className="mt-2 max-w-3xl text-slate-600">{children}</p>}
    </header>
  );
}

