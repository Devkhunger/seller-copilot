import { useState } from "react";
import { api } from "../api/client.js";
import Badge from "../components/Badge.jsx";
import PageHeader from "../components/PageHeader.jsx";

const examples = [
  "What should I promote today?",
  "Which SKU should I pause to reduce losses?",
  "Where is my RTO risk highest?",
  "What are my top 3 actions for tomorrow?"
];

export default function AskCopilot() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  async function ask(event) {
    event?.preventDefault();
    if (!question.trim()) return;
    const current = question.trim();
    setMessages((items) => [...items, { role: "seller", text: current }]);
    setQuestion("");
    setLoading(true);
    try {
      const result = await api.ask(current);
      setMessages((items) => [...items, { role: "copilot", text: result.answer, mode: result.mode }]);
    } catch (error) {
      setMessages((items) => [...items, { role: "copilot", text: error.message, mode: "error" }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader title="Ask Copilot">Ask questions about uploaded orders, SKU scores, RTO risk, promotions, and daily actions.</PageHeader>
      <section className="grid gap-5 xl:grid-cols-[1fr_320px]">
        <div className="card">
          <div className="min-h-[360px] space-y-3">
            {!messages.length && <p className="text-slate-500">Ask a business question after uploading your CSV.</p>}
            {messages.map((message, index) => (
              <div key={index} className={`rounded-lg p-4 ${message.role === "seller" ? "ml-auto max-w-xl bg-merchant text-white" : "mr-auto max-w-3xl bg-slate-100 text-slate-800"}`}>
                <div className="mb-2 flex items-center gap-2">
                  <strong>{message.role === "seller" ? "You" : "Copilot"}</strong>
                  {message.mode && <Badge tone={message.mode === "llm" ? "safe" : "neutral"}>{message.mode === "llm" ? "LLM" : message.mode}</Badge>}
                </div>
                <p className="whitespace-pre-line leading-7">{message.text}</p>
              </div>
            ))}
            {loading && <p className="rounded-lg bg-slate-100 p-4 text-slate-600">Thinking...</p>}
          </div>
          <form onSubmit={ask} className="mt-5 flex gap-3">
            <input className="input" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask: Which SKU should I push today?" />
            <button className="btn" disabled={loading}>Ask</button>
          </form>
        </div>
        <aside className="card">
          <h2 className="text-lg font-black">Try These</h2>
          <div className="mt-3 grid gap-2">
            {examples.map((example) => (
              <button key={example} className="btn-soft text-left" onClick={() => setQuestion(example)}>{example}</button>
            ))}
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            Without an API key, Copilot uses transparent rules. With `OPENAI_API_KEY`, it answers through the LLM service using your dashboard, SKU, RTO, and recommendation context.
          </p>
        </aside>
      </section>
    </>
  );
}
