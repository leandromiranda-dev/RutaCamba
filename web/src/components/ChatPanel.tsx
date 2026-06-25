import * as React from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";
import { chat, ApiError, type ChatMessage } from "@/lib/api";
import { getSession } from "@/lib/session";

/**
 * Panel de guía conversacional. Arranca mostrando la descripción del lugar como
 * primer mensaje y permite chatear de inmediato. El idioma queda fijo (el que se
 * eligió antes de abrir la guía).
 */
export function ChatPanel({
  landmarkId,
  placeName,
  language,
  initialDescription,
  llmAvailable,
}: {
  landmarkId: string;
  placeName: string;
  language: string;
  initialDescription: string;
  llmAvailable: boolean;
}) {
  const [messages, setMessages] = React.useState<ChatMessage[]>([
    { role: "assistant", content: initialDescription },
  ]);
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
      setError(
        e instanceof ApiError && e.status === 503
          ? "El chat no está disponible en este momento."
          : "No se pudo enviar el mensaje. Intentá de nuevo."
      );
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex h-[30rem] flex-col rounded-xl border border-border bg-card">
      {/* Header: lugar */}
      <div className="border-b border-border p-3">
        <p className="truncate font-semibold">{placeName}</p>
        <p className="text-xs text-muted-foreground">Guía turística</p>
      </div>

      {/* Mensajes */}
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}
          >
            <div
              className={cn(
                "max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm leading-relaxed",
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

      {/* Entrada */}
      {llmAvailable ? (
        <div className="flex gap-2 border-t border-border p-3 safe-bottom">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder={`Preguntá sobre ${placeName}…`}
            disabled={sending}
          />
          <Button size="icon" onClick={send} disabled={sending || !input.trim()}>
            <Send className="h-5 w-5" />
          </Button>
        </div>
      ) : (
        <div className="border-t border-border p-3 text-center text-xs text-muted-foreground safe-bottom">
          Chat no disponible (LLM no configurado). Podés leer la información del lugar arriba.
        </div>
      )}
    </div>
  );
}
