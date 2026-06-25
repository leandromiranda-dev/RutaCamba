import * as React from "react";
import { Camera, Languages, BookOpen, MessageCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { CameraCapture, CapturePreview } from "@/components/CameraCapture";
import { LanguageSelect } from "@/components/LanguageSelect";
import { ChatPanel } from "@/components/ChatPanel";
import { useToast } from "@/components/ui/toast";
import {
  predict,
  placeInfo,
  ApiError,
  type PredictResponse,
  type PlaceInfoResponse,
} from "@/lib/api";
import { getSession } from "@/lib/session";
import { cn } from "@/lib/utils";

const STEPS = [
  { icon: Camera, label: "Lugar" },
  { icon: Languages, label: "Idioma" },
  { icon: BookOpen, label: "Info" },
  { icon: MessageCircle, label: "Chat" },
];

export default function Tour() {
  const { notify } = useToast();
  const [step, setStep] = React.useState(0);
  const [shot, setShot] = React.useState<{ blob: Blob; url: string } | null>(null);
  const [loading, setLoading] = React.useState(false);

  const [pred, setPred] = React.useState<PredictResponse | null>(null);
  const [language, setLanguage] = React.useState("es");
  const [info, setInfo] = React.useState<PlaceInfoResponse | null>(null);

  const token = getSession()?.token ?? "";

  const reset = () => {
    setStep(0);
    setShot(null);
    setPred(null);
    setInfo(null);
    setLanguage("es");
  };

  const runPredict = async (blob: Blob) => {
    setLoading(true);
    try {
      const res = await predict(token, blob, 3);
      setPred(res);
      setStep(1);
    } catch (e) {
      notify(
        e instanceof ApiError ? e.message : "No se pudo identificar el lugar.",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  const loadInfo = async () => {
    if (!pred) return;
    setLoading(true);
    try {
      const res = await placeInfo(token, pred.landmark_id, language);
      setInfo(res);
      setStep(2);
    } catch (e) {
      notify(
        e instanceof ApiError ? e.message : "No se pudo obtener la información.",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  const chatAvailable = info?.chat_available ?? pred?.chat_available ?? false;

  return (
    <div className="mx-auto w-full max-w-md space-y-5">
      {/* Stepper */}
      <div className="flex items-center justify-between">
        {STEPS.map((s, i) => {
          const Icon = s.icon;
          const active = i === step;
          const done = i < step;
          const reachable = i <= step;
          const visible = i < 3 || chatAvailable;
          if (!visible) return null;
          return (
            <button
              key={s.label}
              disabled={!reachable}
              onClick={() => reachable && setStep(i)}
              className="flex flex-1 flex-col items-center gap-1"
            >
              <div
                className={cn(
                  "grid h-9 w-9 place-items-center rounded-full border transition-colors",
                  active && "border-primary bg-primary text-primary-foreground",
                  done && "border-primary/50 bg-primary/15 text-primary",
                  !active && !done && "border-border text-muted-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
              </div>
              <span
                className={cn(
                  "text-xs",
                  active ? "text-foreground" : "text-muted-foreground"
                )}
              >
                {s.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* Paso 0: capturar lugar */}
      {step === 0 && (
        <Card className="animate-fade-in">
          <CardContent className="space-y-4 pt-5">
            <h2 className="text-lg font-bold">Identificá un lugar</h2>
            <p className="text-sm text-muted-foreground">
              Tomá una foto del lugar turístico que tenés enfrente.
            </p>
            {shot ? (
              <>
                <CapturePreview url={shot.url} onRetake={() => setShot(null)} />
                <Button
                  className="w-full"
                  size="lg"
                  disabled={loading}
                  onClick={() => runPredict(shot.blob)}
                >
                  {loading ? <Spinner /> : <Camera className="h-5 w-5" />}
                  Identificar lugar
                </Button>
              </>
            ) : (
              <CameraCapture
                facingMode="environment"
                label="Tomar foto"
                onCapture={(blob, url) => setShot({ blob, url })}
              />
            )}
          </CardContent>
        </Card>
      )}

      {/* Paso 1: resultado + idioma */}
      {step === 1 && pred && (
        <Card className="animate-fade-in">
          <CardContent className="space-y-4 pt-5">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold">
                  {pred.translations?.es?.nombre ?? pred.landmark_id}
                </h2>
                <Badge variant="success">
                  {Math.round(pred.confidence * 100)}%
                </Badge>
              </div>
              <div className="flex flex-wrap gap-1">
                {pred.top_k.map(([id, p]) => (
                  <Badge key={id} variant="secondary">
                    {id} · {Math.round(p * 100)}%
                  </Badge>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">
                Elegí un idioma
              </p>
              <LanguageSelect
                value={language}
                onChange={setLanguage}
                llmAvailable={pred.chat_available}
              />
            </div>

            <Button
              className="w-full"
              size="lg"
              disabled={loading}
              onClick={loadInfo}
            >
              {loading ? <Spinner /> : <BookOpen className="h-5 w-5" />}
              Ver información
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Paso 2: info del lugar */}
      {step === 2 && info && (
        <Card className="animate-fade-in">
          <CardContent className="space-y-4 pt-5">
            <h2 className="text-xl font-bold">{info.name}</h2>
            <p className="leading-relaxed text-foreground/90">
              {info.description}
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">{info.language.toUpperCase()}</Badge>
              {info.source === "llm" && <Badge>generado por IA</Badge>}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" className="flex-1" onClick={() => setStep(1)}>
                <Languages className="h-5 w-5" /> Otro idioma
              </Button>
              {chatAvailable && (
                <Button className="flex-1" onClick={() => setStep(3)}>
                  <MessageCircle className="h-5 w-5" /> Conversar
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Paso 3: chat opcional */}
      {step === 3 && info && chatAvailable && (
        <div className="animate-fade-in space-y-3">
          <ChatPanel
            landmarkId={info.landmark_id}
            language={language}
            placeName={info.name}
          />
          <Button variant="outline" className="w-full" onClick={() => setStep(2)}>
            Volver a la información
          </Button>
        </div>
      )}

      <Button variant="ghost" className="w-full" onClick={reset}>
        <RotateCcw className="h-4 w-4" /> Identificar otro lugar
      </Button>
    </div>
  );
}
