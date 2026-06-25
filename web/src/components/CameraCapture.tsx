import * as React from "react";
import Webcam from "react-webcam";
import { Camera, RotateCcw, CameraOff, ImageUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  /** "user" = cámara frontal (selfie), "environment" = trasera (lugar). */
  facingMode?: "user" | "environment";
  onCapture: (blob: Blob, previewUrl: string) => void;
  label?: string;
}

/**
 * Captura de cámara reutilizable. Funciona en navegador y PWA (MediaDevices).
 * Con Capacitor se puede sustituir por @capacitor/camera detrás de esta misma
 * interfaz sin tocar el resto de la app.
 */
export function CameraCapture({
  facingMode = "user",
  onCapture,
  label = "Capturar",
}: Props) {
  const webcamRef = React.useRef<Webcam>(null);
  const fileRef = React.useRef<HTMLInputElement>(null);
  const [denied, setDenied] = React.useState(false);
  const [ready, setReady] = React.useState(false);

  const dataUrlToBlob = (dataUrl: string): Blob => {
    const [head, body] = dataUrl.split(",");
    const mime = head.match(/:(.*?);/)?.[1] ?? "image/jpeg";
    const bin = atob(body);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return new Blob([arr], { type: mime });
  };

  const capture = () => {
    const shot = webcamRef.current?.getScreenshot();
    if (!shot) return;
    onCapture(dataUrlToBlob(shot), shot);
  };

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    onCapture(file, URL.createObjectURL(file));
  };

  if (denied) {
    return (
      <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-card p-6 text-center">
        <CameraOff className="h-10 w-10 text-muted-foreground" />
        <div>
          <p className="font-semibold">Permiso de cámara denegado</p>
          <p className="text-sm text-muted-foreground">
            Habilitá la cámara en los ajustes del navegador, o subí una foto.
          </p>
        </div>
        <Button variant="outline" onClick={() => fileRef.current?.click()}>
          <ImageUp className="h-5 w-5" /> Subir foto
        </Button>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          capture={facingMode}
          className="hidden"
          onChange={onFile}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="relative aspect-[3/4] w-full overflow-hidden rounded-xl border border-border bg-black">
        <Webcam
          ref={webcamRef}
          audio={false}
          screenshotFormat="image/jpeg"
          screenshotQuality={0.9}
          mirrored={facingMode === "user"}
          videoConstraints={{ facingMode }}
          onUserMedia={() => setReady(true)}
          onUserMediaError={() => setDenied(true)}
          className="h-full w-full object-cover"
        />
        {!ready && (
          <div className="absolute inset-0 grid place-items-center text-sm text-muted-foreground">
            Iniciando cámara…
          </div>
        )}
      </div>
      <div className="flex gap-2">
        <Button className="flex-1" size="lg" onClick={capture} disabled={!ready}>
          <Camera className="h-5 w-5" /> {label}
        </Button>
        <Button
          variant="outline"
          size="lg"
          onClick={() => fileRef.current?.click()}
          aria-label="Subir foto"
        >
          <ImageUp className="h-5 w-5" />
        </Button>
      </div>
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        capture={facingMode}
        className="hidden"
        onChange={onFile}
      />
    </div>
  );
}

/** Vista previa de una captura, con opción de volver a tomar. */
export function CapturePreview({
  url,
  onRetake,
}: {
  url: string;
  onRetake: () => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="aspect-[3/4] w-full overflow-hidden rounded-xl border border-border bg-black">
        <img src={url} alt="captura" className="h-full w-full object-cover" />
      </div>
      <Button variant="outline" size="lg" onClick={onRetake}>
        <RotateCcw className="h-5 w-5" /> Volver a tomar
      </Button>
    </div>
  );
}
