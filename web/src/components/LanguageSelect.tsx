import { cn } from "@/lib/utils";

export interface Language {
  code: string;
  label: string;
  flag: string;
  offline: boolean;
}

// es/en/fr/it tienen traducción pre-generada (offline). El resto requiere LLM.
export const LANGUAGES: Language[] = [
  { code: "es", label: "Español", flag: "🇪🇸", offline: true },
  { code: "en", label: "English", flag: "🇬🇧", offline: true },
  { code: "fr", label: "Français", flag: "🇫🇷", offline: true },
  { code: "it", label: "Italiano", flag: "🇮🇹", offline: true },
  { code: "pt", label: "Português", flag: "🇧🇷", offline: false },
  { code: "de", label: "Deutsch", flag: "🇩🇪", offline: false },
];

export function LanguageSelect({
  value,
  onChange,
  llmAvailable,
}: {
  value: string;
  onChange: (code: string) => void;
  llmAvailable: boolean;
}) {
  const options = LANGUAGES.filter((l) => l.offline || llmAvailable);
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {options.map((l) => (
        <button
          key={l.code}
          onClick={() => onChange(l.code)}
          className={cn(
            "flex items-center gap-2 rounded-lg border px-3 py-3 text-left transition-colors",
            value === l.code
              ? "border-primary bg-primary/15"
              : "border-border bg-secondary/40 hover:bg-secondary/70"
          )}
        >
          <span className="text-xl">{l.flag}</span>
          <span className="text-sm font-medium">{l.label}</span>
        </button>
      ))}
    </div>
  );
}
