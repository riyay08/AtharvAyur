import { useCallback, useRef, useState } from "react";
import { Loader2, MessageCircle, Send } from "lucide-react";
import { sendChatMessage } from "../api";

/**
 * @param {{ userId: string | null }} props
 */
export function HealthChat({ userId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || !userId || loading) return;
    setError(null);
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    setLoading(true);
    try {
      const data = await sendChatMessage(userId, text);
      if (data.blocked) {
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            text: data.response_text || data.reply || "This message could not be processed.",
            blocked: true,
            safetyReason: data.safety_reason,
            matchedTerms: data.matched_terms,
          },
        ]);
      } else {
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            text: data.response_text || data.reply || "",
            citations: data.citations || [],
            webSearchQueries: data.web_search_queries || [],
            modelSafety: data.blocked_by_model_safety,
          },
        ]);
      }
      requestAnimationFrame(scrollToBottom);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chat failed");
      setMessages((m) => m.slice(0, -1));
      setInput(text);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (ev) => {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      handleSend();
    }
  };

  if (!userId) {
    return (
      <div className="rounded-2xl border border-dashed border-emerald-500/25 bg-emerald-500/5 p-8 text-center text-slate-400">
        <MessageCircle className="mx-auto mb-3 text-emerald-400/50" size={36} />
        <p className="text-sm font-medium text-slate-200">HolisticAI chat</p>
        <p className="mt-1 text-sm text-slate-500">
          Save your quiz results with the button above to create your profile and unlock the assistant.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col overflow-hidden rounded-2xl border border-white/[0.08] bg-black/20 shadow-[0_20px_50px_rgba(0,0,0,0.35)] backdrop-blur-md">
      <div className="border-b border-white/10 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-100">HolisticAI Health</h3>
        <p className="text-xs text-slate-500">Non-diagnostic wellness assistant (grounded search when relevant)</p>
      </div>

      <div className="max-h-[min(420px,55vh)] min-h-[200px] space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-center text-sm text-slate-500">
            Ask a general wellness question. Emergency or crisis language will be blocked before any AI runs.
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[90%] rounded-2xl px-4 py-2 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "border border-emerald-500/35 bg-emerald-500/15 text-emerald-50 shadow-[0_0_24px_rgba(52,211,153,0.12)]"
                  : msg.blocked
                    ? "border border-amber-400/35 bg-amber-500/10 text-amber-100"
                    : "border border-white/10 bg-white/[0.06] text-slate-200"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>
              {msg.safetyReason && (
                <p className="mt-2 text-xs text-amber-200/80">Reason: {msg.safetyReason}</p>
              )}
              {msg.matchedTerms?.length > 0 && (
                <p className="mt-1 text-xs text-amber-200/70">Matched: {msg.matchedTerms.join(", ")}</p>
              )}
              {msg.citations?.length > 0 && (
                <ul className="mt-3 space-y-1 border-t border-white/10 pt-2 text-xs">
                  <li className="font-medium text-emerald-400/90">Sources</li>
                  {msg.citations.map((c, j) => (
                    <li key={j}>
                      <a
                        href={c.url || c.uri}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-emerald-300/90 underline decoration-emerald-500/40 underline-offset-2 transition hover:text-emerald-200"
                      >
                        {c.source_name || c.title || c.url || c.uri}
                      </a>
                    </li>
                  ))}
                </ul>
              )}
              {msg.webSearchQueries?.length > 0 && (
                <p className="mt-2 text-xs text-slate-500">
                  Search queries: {msg.webSearchQueries.join(" · ")}
                </p>
              )}
              {msg.modelSafety && (
                <p className="mt-2 text-xs text-amber-300/80">
                  Note: reply may have been limited by model safety filters.
                </p>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-2 text-sm text-slate-400">
              <Loader2 className="animate-spin text-emerald-400/80" size={16} />
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="border-t border-rose-500/25 bg-rose-950/40 px-4 py-2 text-sm text-rose-200">{error}</div>
      )}

      <div className="flex gap-2 border-t border-white/10 bg-black/20 p-3">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
          placeholder="Type a message…"
          className="min-h-[44px] flex-1 resize-none rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 outline-none transition focus:border-emerald-500/40 focus:ring-2 focus:ring-emerald-500/20"
          disabled={loading}
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="inline-flex shrink-0 items-center justify-center gap-2 self-end rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 px-4 py-2 text-sm font-medium text-emerald-950 shadow-lg shadow-emerald-900/30 transition hover:from-emerald-500 hover:to-emerald-400 disabled:opacity-50"
        >
          <Send size={16} />
          Send
        </button>
      </div>
    </div>
  );
}
