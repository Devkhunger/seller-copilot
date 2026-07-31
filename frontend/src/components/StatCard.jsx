const accents = ["from-emerald-500 to-teal-700", "from-sky-500 to-blue-700", "from-amber-400 to-orange-600", "from-rose-400 to-red-600", "from-violet-500 to-indigo-700"];

export default function StatCard({ label, value, index = 0 }) {
  return (
    <div className="stat-card group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className={`absolute right-0 top-0 h-20 w-20 -translate-y-7 translate-x-7 rounded-full bg-gradient-to-br ${accents[index % accents.length]} opacity-10 transition duration-500 group-hover:scale-150`} />
      <div className="relative">
        <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p>
        <p className="mt-2 text-3xl font-extrabold tracking-tight text-ink">{value}</p>
        <div className="mt-3 h-1 w-10 rounded-full bg-emerald-500 transition-all duration-300 group-hover:w-16" />
      </div>
    </div>
  );
}
