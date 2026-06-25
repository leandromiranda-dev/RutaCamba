import * as React from "react";
import { Navigate } from "react-router-dom";
import { MapPinned, Users } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { EnrollForm } from "@/components/EnrollForm";
import { isAdmin } from "@/lib/session";
import { cn } from "@/lib/utils";
import Tour from "./Tour";

type Tab = "tour" | "enroll";

export default function Admin() {
  const [tab, setTab] = React.useState<Tab>("enroll");

  // Guard de ruta: si no es admin, al tour.
  if (!isAdmin()) return <Navigate to="/tour" replace />;

  return (
    <div className="mx-auto w-full max-w-md space-y-5">
      <div className="grid grid-cols-2 gap-2 rounded-xl border border-border bg-card p-1">
        {(
          [
            { id: "tour", label: "Turismo", icon: MapPinned },
            { id: "enroll", label: "Administración", icon: Users },
          ] as { id: Tab; label: string; icon: typeof Users }[]
        ).map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                "flex items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                tab === t.id
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-secondary/60"
              )}
            >
              <Icon className="h-4 w-4" />
              {t.label}
            </button>
          );
        })}
      </div>

      {tab === "tour" ? (
        <Tour />
      ) : (
        <Card className="animate-fade-in">
          <CardContent className="space-y-4 pt-5">
            <div>
              <h2 className="text-lg font-bold">Registrar nueva persona</h2>
              <p className="text-sm text-muted-foreground">
                Agregá su rostro y rol para que pueda autenticarse luego.
              </p>
            </div>
            <EnrollForm />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
