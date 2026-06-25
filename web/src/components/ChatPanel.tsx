import * as React from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";
import { chat, ApiError, type ChatMessage } from "@/lib/api";
import { getSession } from "@/lib/session";

export function ChatPanel({
  landmarkId,
  language,
  placeName,
}: {
  landmarkId: string;
  language: string;
  placeName: string;
}) {
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [input, setInput] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const endRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const send = async () => {
    const text = input.trim();
    const token = getSession()?.token;
    if (!text || !token || sending) return;

    const history = messages;
    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setSending(true);
    setError(null);
    try {
      const res = await chat(token, landmarkId, language, text, history);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
    } catch (e) {
      const msg =
        e instanceof ApiError && e.status === 503
          ? "El chat no está disponible en este momento."
          : "No se pudo enviar el mensaje. Intentá de nuevo.";
      setError(msg);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex h-[26rem] flex-col rounded-xl border border-border bg-card">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-center text-sm text-muted-foreground">
            Preguntá lo que quieras sobre {placeName}.
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={cn(
              "flex",
              m.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            <div
              className={cn(
                "max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm",
                m.role === "user"
                  ? "bg-primary text-primary-foreground rounded-br-sm"
                  : "bg-secondary text-secondary-foreground rounded-bl-sm"
              )}
            >
              {m.content}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Spinner className="h-4 w-4" /> escribiendo…
          </div>
        )}
        {error && <p className="text-center text-sm text-red-400">{error}</p>}
        <div ref={endRef} />
      </div>
      <div className="flex gap-2 border-t border-border p-3 safe-bottom">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Escribí tu pregunta…"
          disabled={sending}
        />
        <Button size="icon" onClick={send} disabled={sending || !input.trim()}>
          <Send className="h-5 w-5" />
        </Button>
      </div>
    </div>
  );
}
