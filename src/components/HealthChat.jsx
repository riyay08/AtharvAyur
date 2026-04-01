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
            text: data.reply || "This message could not be processed.",
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
            text: data.reply || "",
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
      <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 p-8 text-center text-slate-600">
        <MessageCircle className="mx-auto mb-3 text-slate-400" size={36} />
        <p className="text-sm font-medium text-slate-700">HolisticAI chat</p>
        <p className="mt-1 text-sm">
          Save your quiz results with the button above to create your profile and unlock the assistant.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col rounded-2xl border border-slate-200/70 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-900">HolisticAI Health</h3>
        <p className="text-xs text-slate-500">Non-diagnostic wellness assistant (grounded search when relevant)</p>
      </div>

      <div className="max-h-[min(420px,55vh)] min-h-[200px] space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-center text-sm text-slate-500">
            Ask a general wellness question. Emergency or crisis language will be blocked before any AI runs.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[90%] rounded-2xl px-4 py-2 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-slate-900 text-white"
                  : msg.blocked
                    ? "border border-amber-200 bg-amber-50 text-amber-950"
                    : "border border-slate-200 bg-slate-50 text-slate-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>
              {msg.safetyReason && (
                <p className="mt-2 text-xs opacity-90">Reason: {msg.safetyReason}</p>
              )}
              {msg.matchedTerms?.length > 0 && (
                <p className="mt-1 text-xs opacity-90">Matched: {msg.matchedTerms.join(", ")}</p>
              )}
              {msg.citations?.length > 0 && (
                <ul className="mt-3 space-y-1 border-t border-slate-200/80 pt-2 text-xs">
                  <li className="font-medium text-slate-600">Sources</li>
                  {msg.citations.map((c, j) => (
                    <li key={j}>
                      <a
                        href={c.uri}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-cyan-700 underline hover:text-cyan-900"
                      >
                        {c.title || c.uri}
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
                <p className="mt-2 text-xs text-amber-800">Note: reply may have been limited by model safety filters.</p>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-600">
              <Loader2 className="animate-spin" size={16} />
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="border-t border-red-100 bg-red-50 px-4 py-2 text-sm text-red-800">{error}</div>
      )}

      <div className="flex gap-2 border-t border-slate-100 p-3">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
          placeholder="Type a message…"
          className="min-h-[44px] flex-1 resize-none rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none ring-slate-400 focus:ring-2"
          disabled={loading}
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="inline-flex shrink-0 items-center justify-center gap-2 self-end rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-50"
        >
          <Send size={16} />
          Send
        </button>
      </div>
    </div>
  );
}
