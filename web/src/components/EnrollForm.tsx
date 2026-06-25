import * as React from "react";
import { UserPlus, Trash2, ShieldCheck, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { CameraCapture } from "@/components/CameraCapture";
import { useToast } from "@/components/ui/toast";
import { enroll, ApiError } from "@/lib/api";
import { getSession, type Role } from "@/lib/session";
import { cn } from "@/lib/utils";

interface Shot {
  blob: Blob;
  url: string;
}

export function EnrollForm() {
  const { notify } = useToast();
  const [name, setName] = React.useState("");
  const [role, setRole] = React.useState<Role>("user");
  const [shots, setShots] = React.useState<Shot[]>([]);
  const [submitting, setSubmitting] = React.useState(false);

  const addShot = (blob: Blob, url: string) =>
    setShots((s) => [...s, { blob, url }]);
  const removeShot = (i: number) =>
    setShots((s) => s.filter((_, idx) => idx !== i));

  const submit = async () => {
    const token = getSession()?.token;
    if (!token) return;
    if (!name.trim()) return notify("Ingresá un nombre.", "error");
    if (shots.length === 0)
      return notify("Capturá al menos una foto del rostro.", "error");

    setSubmitting(true);
    try {
      const res = await enroll(
        token,
        name.trim(),
        role,
        shots.map((s) => s.blob)
      );
      notify(
        `"${res.identity}" registrado/a (${res.embeddings_added} rostro(s)).`,
        "success"
      );
      setName("");
      setShots([]);
      setRole("user");
    } catch (e) {
      const msg =
        e instanceof ApiError ? e.message : "No se pudo registrar a la persona.";
      notify(msg, "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <Label htmlFor="enroll-name">Nombre de la persona</Label>
        <Input
          id="enroll-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="ej. maria"
        />
      </div>

      <div className="space-y-2">
        <Label>Rol</Label>
        <div className="grid grid-cols-2 gap-2">
          {(["user", "admin"] as Role[]).map((r) => (
            <button
              key={r}
              onClick={() => setRole(r)}
              className={cn(
                "flex items-center justify-center gap-2 rounded-lg border px-3 py-3 text-sm font-medium transition-colors",
                role === r
                  ? "border-primary bg-primary/15"
                  : "border-border bg-secondary/40 hover:bg-secondary/70"
              )}
            >
              {r === "admin" ? (
                <ShieldCheck className="h-4 w-4" />
              ) : (
                <User className="h-4 w-4" />
              )}
              {r === "admin" ? "Administrador" : "Usuario"}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Fotos del rostro ({shots.length})</Label>
        {shots.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {shots.map((s, i) => (
              <div key={i} className="relative">
                <img
                  src={s.url}
                  alt={`rostro ${i + 1}`}
                  className="h-20 w-20 rounded-lg border border-border object-cover"
                />
                <button
                  onClick={() => removeShot(i)}
                  className="absolute -right-2 -top-2 rounded-full bg-destructive p-1"
                  aria-label="Quitar"
                >
                  <Trash2 className="h-3.5 w-3.5 text-white" />
                </button>
              </div>
            ))}
          </div>
        )}
        <CameraCapture
          facingMode="user"
          label="Agregar rostro"
          onCapture={addShot}
        />
      </div>

      <Button className="w-full" size="lg" onClick={submit} disabled={submitting}>
        {submitting ? <Spinner /> : <UserPlus className="h-5 w-5" />}
        Registrar persona
      </Button>
    </div>
  );
}
