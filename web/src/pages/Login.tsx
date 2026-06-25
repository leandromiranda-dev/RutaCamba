import * as React from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, ShieldX, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { CameraCapture, CapturePreview } from "@/components/CameraCapture";
import { verify, ApiError } from "@/lib/api";
import { saveSession } from "@/lib/session";

export default function Login() {
  const nav = useNavigate();
  const [name, setName] = React.useState("");
  const [selfie, setSelfie] = React.useState<{ blob: Blob; url: string } | null>(
    null
  );
  const [loading, setLoading] = React.useState(false);
  const [denied, setDenied] = React.useState<string | null>(null);

  const submit = async () => {
    if (!name.trim() || !selfie) return;
    setLoading(true);
    setDenied(null);
    try {
      const res = await verify(name.trim(), selfie.blob);
      saveSession({
        token: res.token,
        identity: res.identity,
        role: res.role,
      });
      nav(res.role === "admin" ? "/admin" : "/tour", { replace: true });
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        // Por seguridad NO revelamos a qué identidad se parece el rostro:
        // delataría qué nombre declarar para usurpar una identidad.
        setDenied(
          `Acceso denegado: el rostro no coincide con "${name}". ` +
            `Verificá tu nombre e intentá de nuevo con buena iluminación.`
        );
      } else {
        setDenied(
          e instanceof ApiError ? e.message : "No se pudo conectar con el servidor."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-md flex-col px-4 py-8 safe-top safe-bottom">
      <header className="mb-6 flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-xl bg-primary/20">
          <MapPin className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-bold">RutaCamba</h1>
          <p className="text-sm text-muted-foreground">
            Guía turística de Santa Cruz
          </p>
        </div>
      </header>

      <Card className="animate-fade-in">
        <CardContent className="space-y-5 pt-5">
          <div className="space-y-2">
            <Label htmlFor="name">Tu nombre</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="ej. jose"
              autoCapitalize="none"
            />
          </div>

          <div className="space-y-2">
            <Label>Selfie de verificación</Label>
            {selfie ? (
              <CapturePreview url={selfie.url} onRetake={() => setSelfie(null)} />
            ) : (
              <CameraCapture
                facingMode="user"
                label="Tomar selfie"
                onCapture={(blob, url) => setSelfie({ blob, url })}
              />
            )}
          </div>

          {denied && (
            <div className="flex items-start gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm">
              <ShieldX className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
              <span>{denied}</span>
            </div>
          )}

          <Button
            className="w-full"
            size="lg"
            onClick={submit}
            disabled={loading || !name.trim() || !selfie}
          >
            {loading ? <Spinner /> : <ShieldCheck className="h-5 w-5" />}
            Verificar identidad
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
