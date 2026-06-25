import * as React from "react";
import { Camera, Languages, MessageCircle, RotateCcw } from "lucide-react";
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
  { icon: MessageCircle, label: "Guía" },
];

// Confianza mínima del clasificador para dar por reconocido el lugar. El modelo
// es de conjunto cerrado (8 clases) y SIEMPRE elige una, incluso ante una foto
// que no es ningún lugar (p. ej. un rostro). Por eso, por debajo de este umbral
// asumimos que no es ninguno de los lugares conocidos y pedimos otra foto.
// Ajustá según los resultados reales (ver la confianza que muestra el aviso).
const MIN_CONFIDENCE = 0.7;

export default function Tour() {
  const { notify } = useToast();
  const [step, setStep] = React.useState(0);
  const [shot, setShot] = React.useState<{ blob: Blob; url: string } | null>(null);
  const [loading, setLoading] = React.useState(false);

  const [pred, setPred] = React.useState<PredictResponse | null>(null);
  const [language, setLanguage] = React.useState("es");
  const [info, setInfo] = React.useState<PlaceInfoResponse | null>(null);
  const [notRecognized, setNotRecognized] = React.useState(false);
  const [rejectedConf, setRejectedConf] = React.useState<number | null>(null);

  const token = getSession()?.token ?? "";

  const reset = () => {
    setStep(0);
    setShot(null);
    setPred(null);
    setInfo(null);
    setNotRecognized(false);
    setRejectedConf(null);
    setLanguage("es");
  };

  const runPredict = async (blob: Blob) => {
    setLoading(true);
    setNotRecognized(false);
    try {
      const res = await predict(token, blob, 3);
      // Si el clasificador no está suficientemente seguro, no es ninguno de los
      // lugares conocidos → pedimos otra foto en vez de mostrar algo incorrecto.
      if (res.confidence < MIN_CONFIDENCE) {
        setRejectedConf(res.confidence);
        setNotRecognized(true);
        return;
      }
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

  // Carga la info del lugar en el idioma elegido y abre la guía (chat).
  const openGuide = async () => {
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

  return (
    <div className="mx-auto w-full max-w-md space-y-5">
      {/* Stepper */}
      <div className="flex items-center justify-between">
        {STEPS.map((s, i) => {
          const Icon = s.icon;
          const active = i === step;
          const done = i < step;
          const reachable = i <= step;
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
              <span className={cn("text-xs", active ? "text-foreground" : "text-muted-foreground")}>
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
                <CapturePreview
                  url={shot.url}
                  onRetake={() => {
                    setShot(null);
                    setNotRecognized(false);
                    setRejectedConf(null);
                  }}
                />
                {notRecognized && (
                  <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm">
                    No se tiene información de este lugar: no coincide con ninguno
                    de los lugares conocidos. Probá con otra foto, enfocando bien
                    el lugar y con buena iluminación.
                    {rejectedConf !== null && (
                      <span className="mt-1 block text-xs text-muted-foreground">
                        (confianza detectada: {Math.round(rejectedConf * 100)}%)
                      </span>
                    )}
                  </div>
                )}
                <Button
                  className="w-full"
                  size="lg"
                  disabled={loading}
                  onClick={() => runPredict(shot.blob)}
                >
                  {loading ? <Spinner /> : <Camera className="h-5 w-5" />}
                  {notRecognized ? "Reintentar" : "Identificar lugar"}
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
                <Badge variant="success">{Math.round(pred.confidence * 100)}%</Badge>
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
              <p className="text-sm font-medium text-muted-foreground">Elegí un idioma</p>
              <LanguageSelect
                value={language}
                onChange={setLanguage}
                llmAvailable={pred.chat_available}
              />
            </div>

            <Button className="w-full" size="lg" disabled={loading} onClick={openGuide}>
              {loading ? <Spinner /> : <MessageCircle className="h-5 w-5" />}
              Abrir guía
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Paso 2: guía conversacional (descripción + chat, con cambio de idioma) */}
      {step === 2 && info && (
        <div className="animate-fade-in space-y-3">
          <ChatPanel
            landmarkId={info.landmark_id}
            placeName={info.name}
            language={info.language}
            initialDescription={info.description}
            llmAvailable={info.chat_available}
          />
        </div>
      )}

      <Button variant="ghost" className="w-full" onClick={reset}>
        <RotateCcw className="h-4 w-4" /> Identificar otro lugar
      </Button>
    </div>
  );
}
