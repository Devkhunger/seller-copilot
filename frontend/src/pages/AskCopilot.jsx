import { useRef, useState } from "react";
import { api } from "../api/client.js";
import Badge from "../components/Badge.jsx";
import PageHeader from "../components/PageHeader.jsx";

const examples = [
  { icon: "📈", label: "What should I promote today?", hint: "Find your best growth opportunity" },
  { icon: "🧯", label: "Which SKU should I pause to reduce losses?", hint: "Spot products hurting your margin" },
  { icon: "📦", label: "Where is my RTO risk highest?", hint: "See risky states and products" },
  { icon: "✅", label: "What are my top 3 actions for tomorrow?", hint: "Get a focused plan for the day" },
];

export default function AskCopilot() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);

  async function ask(event) {
    event?.preventDefault();
    if (!question.trim() || loading) return;
    const current = question.trim();
    setMessages((items) => [...items, { role: "seller", text: current }]);
    setQuestion("");
    setLoading(true);
    try {
      const result = await api.ask(current);
      setMessages((items) => [...items, { role: "copilot", text: result.answer }]);
    } catch (error) {
      setMessages((items) => [...items, { role: "copilot", text: error.message, mode: "error" }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function useExample(example) {
    setQuestion(example);
    inputRef.current?.focus();
  }

  return (
    <>
      <PageHeader title="Ask Copilot">Get clear, practical answers about your orders, products, returns, and next best actions.</PageHeader>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-emerald-50 to-white px-5 py-4">
            <div className="flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-merchant text-xl text-white shadow-sm">✦</div>
              <div>
                <h2 className="font-black text-slate-900">Your business assistant</h2>
                <p className="text-sm text-slate-500">Personalised to the data you uploaded</p>
              </div>
            </div>
            {messages.length > 0 && (
              <button type="button" className="text-sm font-semibold text-slate-500 hover:text-slate-900" onClick={() => setMessages([])}>
                Clear chat
              </button>
            )}
          </div>

          <div className="min-h-[390px] space-y-4 p-5">
            {!messages.length && (
              <div className="grid min-h-[320px] place-items-center text-center">
                <div className="max-w-md">
                  <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-emerald-50 text-3xl">💬</div>
                  <h3 className="mt-4 text-xl font-black text-slate-900">What would you like to improve?</h3>
                  <p className="mt-2 leading-6 text-slate-500">Ask in plain language. Copilot will use your uploaded business data to point you towards the next useful decision.</p>
                </div>
              </div>
            )}
            {messages.map((message, index) => (
              <div key={index} className={`flex gap-3 ${message.role === "seller" ? "justify-end" : "justify-start"}`}>
                {message.role === "copilot" && <div className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-emerald-100 text-sm">✦</div>}
                <div className={`max-w-2xl rounded-2xl px-4 py-3 ${message.role === "seller" ? "rounded-br-sm bg-merchant text-white" : "rounded-bl-sm bg-slate-100 text-slate-800"}`}>
                  <div className="mb-1 flex items-center gap-2 text-xs font-bold uppercase tracking-wide opacity-70">
                    {message.role === "seller" ? "You" : "Copilot"}
                    {message.mode === "error" && <Badge tone="risk">Needs attention</Badge>}
                  </div>
                  <p className="whitespace-pre-line leading-7">{message.text}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-3">
                <div className="grid h-8 w-8 place-items-center rounded-lg bg-emerald-100 text-sm">✦</div>
                <p className="rounded-2xl rounded-bl-sm bg-slate-100 px-4 py-3 text-slate-600">Thinking...</p>
              </div>
            )}
          </div>

          <form onSubmit={ask} className="border-t border-slate-100 bg-slate-50 p-4">
            <div className="flex items-end gap-3 rounded-xl border border-slate-200 bg-white p-2 shadow-sm focus-within:border-merchant focus-within:ring-4 focus-within:ring-merchant/10">
              <textarea
                ref={inputRef}
                className="min-h-[44px] flex-1 resize-none border-0 bg-transparent px-2 py-2 text-sm outline-none"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); ask(event); } }}
                placeholder="Ask about your business..."
                rows={1}
              />
              <button className="btn shrink-0" disabled={loading || !question.trim()}>{loading ? "Thinking..." : "Ask"}</button>
            </div>
            <p className="mt-2 px-2 text-xs text-slate-400">Press Enter to ask · Shift + Enter for a new line</p>
          </form>
        </div>

        <aside className="card h-fit">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-wide text-merchant">Quick start</p>
              <h2 className="mt-1 text-xl font-black text-slate-900">Try a question</h2>
            </div>
            <span className="text-2xl">⚡</span>
          </div>
          <div className="mt-4 grid gap-2">
            {examples.map((example) => (
              <button key={example.label} type="button" className="group rounded-xl border border-slate-200 p-3 text-left transition hover:border-emerald-300 hover:bg-emerald-50/60" onClick={() => useExample(example.label)}>
                <span className="flex items-start gap-3">
                  <span className="text-lg">{example.icon}</span>
                  <span>
                    <span className="block text-sm font-bold leading-5 text-slate-800 group-hover:text-emerald-900">{example.label}</span>
                    <span className="mt-1 block text-xs text-slate-500">{example.hint}</span>
                  </span>
                </span>
              </button>
            ))}
          </div>
          <div className="mt-5 rounded-xl bg-slate-50 p-4">
            <p className="text-sm font-bold text-slate-800">Make your question specific</p>
            <p className="mt-1 text-sm leading-6 text-slate-500">Mention a product, state, date range, or goal to get a more useful answer.</p>
          </div>
        </aside>
      </section>
    </>
  );
}
