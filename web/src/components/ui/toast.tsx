import * as React from "react";
import { CheckCircle2, XCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastKind = "success" | "error" | "info";
interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

interface ToastCtx {
  notify: (message: string, kind?: ToastKind) => void;
}

const Ctx = React.createContext<ToastCtx | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const notify = React.useCallback(
    (message: string, kind: ToastKind = "info") => {
      const id = Date.now() + Math.random();
      setToasts((t) => [...t, { id, kind, message }]);
      setTimeout(
        () => setToasts((t) => t.filter((x) => x.id !== id)),
        4000
      );
    },
    []
  );

  const dismiss = (id: number) =>
    setToasts((t) => t.filter((x) => x.id !== id));

  return (
    <Ctx.Provider value={{ notify }}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 top-0 z-50 flex flex-col items-center gap-2 p-3 safe-top">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-lg border bg-card p-3 shadow-xl animate-fade-in",
              t.kind === "success" && "border-emerald-500/40",
              t.kind === "error" && "border-destructive/50",
              t.kind === "info" && "border-border"
            )}
          >
            {t.kind === "success" && (
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
            )}
            {t.kind === "error" && (
              <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
            )}
            <p className="flex-1 text-sm">{t.message}</p>
            <button onClick={() => dismiss(t.id)} aria-label="Cerrar">
              <X className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}

export function useToast(): ToastCtx {
  const ctx = React.useContext(Ctx);
  if (!ctx) throw new Error("useToast debe usarse dentro de <ToastProvider>");
  return ctx;
}
