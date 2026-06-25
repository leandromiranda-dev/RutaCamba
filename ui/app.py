"""ui/app.py — Interfaz Gradio de RutaCamba (Nicole, Fase 6).

Diseño basado en Lumina Velocity (desing/):
  - Tab 1 ← inicio_y_autenticaci_n_facial
  - Tab 2 ← esc_ner_del_entorno + an_lisis_y_resultados

La UI consume la API con requests y NUNCA carga modelos directamente.
"""
import os

import gradio as gr
import requests

API_URL = os.environ.get("API_URL", "http://localhost:8000")

# ── Head: Tailwind CDN + config exacto de desing/ + Material Symbols + Fonts ──

_HEAD = """
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Montserrat:wght@600;700&display=swap" rel="stylesheet"/>
<script id="tw-config">
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "surface":                   "#f7f9fb",
        "surface-dim":               "#d8dadc",
        "surface-container-lowest":  "#ffffff",
        "surface-container-low":     "#f2f4f6",
        "surface-container":         "#eceef0",
        "surface-container-high":    "#e6e8ea",
        "surface-container-highest": "#e0e3e5",
        "surface-tint":              "#3a5f94",
        "on-surface":                "#191c1e",
        "on-surface-variant":        "#43474f",
        "outline":                   "#737780",
        "outline-variant":           "#c3c6d1",
        "primary":                   "#001e40",
        "on-primary":                "#ffffff",
        "primary-container":         "#003366",
        "on-primary-container":      "#799dd6",
        "primary-fixed-dim":         "#a7c8ff",
        "secondary":                 "#00696e",
        "on-secondary":              "#ffffff",
        "secondary-container":       "#00f4fe",
        "on-secondary-container":    "#006c71",
        "secondary-fixed-dim":       "#00dce5",
        "background":                "#f7f9fb",
        "on-background":             "#191c1e",
        "error":                     "#ba1a1a",
        "on-error":                  "#ffffff",
        "error-container":           "#ffdad6",
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "lg":   "0.5rem",
        "xl":   "0.75rem",
        "full": "9999px"
      },
      spacing: {
        "margin-mobile":  "16px",
        "base":           "8px",
        "margin-desktop": "40px",
        "gutter":         "24px",
      },
      fontFamily: {
        "body-md":            ["Inter"],
        "caption":            ["Inter"],
        "headline-md":        ["Montserrat"],
        "label-md":           ["Inter"],
        "display-lg":         ["Montserrat"],
        "body-lg":            ["Inter"],
        "headline-lg":        ["Montserrat"],
        "headline-lg-mobile": ["Montserrat"],
      },
      fontSize: {
        "body-md":            ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "caption":            ["12px", { lineHeight: "16px", fontWeight: "400" }],
        "headline-md":        ["24px", { lineHeight: "32px", fontWeight: "600" }],
        "label-md":           ["14px", { lineHeight: "20px", fontWeight: "600" }],
        "display-lg":         ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "body-lg":            ["18px", { lineHeight: "28px", fontWeight: "400" }],
        "headline-lg":        ["32px", { lineHeight: "40px", fontWeight: "600" }],
        "headline-lg-mobile": ["28px", { lineHeight: "36px", fontWeight: "600" }],
      }
    }
  }
}
</script>
<style>
  /* Glass overlay (desing/ glass-overlay) */
  .glass-overlay {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 0.5px solid rgba(255, 255, 255, 0.3);
  }
  /* Gradient text (desing/ ai-gradient-text) */
  .ai-gradient-text {
    background: linear-gradient(135deg, #001e40 0%, #00696e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  /* Scan line — sweep once, pause, repeat (no distracting infinite loop) */
  .scan-line {
    width: 100%;
    height: 2px;
    background: linear-gradient(to right, transparent, #00dce5, transparent);
    position: absolute;
    animation: scan 5s ease-in-out infinite;
    will-change: top, opacity;
  }
  @keyframes scan {
    0%   { top: 10%; opacity: 0; }
    8%   { opacity: 0.8; }
    42%  { top: 90%; opacity: 0.8; }
    50%  { top: 90%; opacity: 0; }
    100% { top: 90%; opacity: 0; }
  }
  /* Pulse ring — slower, subtler */
  .pulse-ring {
    position: absolute;
    width: 100%; height: 100%;
    border-radius: 50%;
    border: 1.5px solid #00dce5;
    animation: pulse-anim 3.5s ease-out infinite;
    opacity: 0;
  }
  @keyframes pulse-anim {
    0%   { transform: scale(0.95); opacity: 0.4; }
    60%  { transform: scale(1.4);  opacity: 0; }
    100% { transform: scale(1.4);  opacity: 0; }
  }
  /* Scanner frame corners (desing/ esc_ner_del_entorno) */
  .scanner-frame { position: relative; }
  .scanner-frame::before, .scanner-frame::after,
  .scanner-frame > div::before, .scanner-frame > div::after {
    content: '';
    position: absolute;
    width: 30px; height: 30px;
    border-color: #00dce5;
    border-style: solid;
  }
  .scanner-frame::before     { top: 0;    left: 0;  border-width: 3px 0 0 3px; }
  .scanner-frame::after      { top: 0;    right: 0; border-width: 3px 3px 0 0; }
  .scanner-frame > div::before { bottom: 0; left: 0;  border-width: 0 0 3px 3px; }
  .scanner-frame > div::after  { bottom: 0; right: 0; border-width: 0 3px 3px 0; }
  /* Scanline camera — sweep+pause pattern, WCAG motion-friendly */
  @keyframes scanline {
    0%   { transform: translateY(0);    opacity: 0; }
    8%   { opacity: 0.75; }
    42%  { transform: translateY(250px); opacity: 0.75; }
    50%  { transform: translateY(250px); opacity: 0; }
    100% { transform: translateY(250px); opacity: 0; }
  }
  .scan-line-cam {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(to right, transparent, #00dce5, transparent);
    box-shadow: 0 0 6px rgba(0,220,229,.5);
    animation: scanline 5s ease-in-out infinite;
    will-change: transform, opacity;
  }
  /* Accessibility: stop all decorative motion */
  @media (prefers-reduced-motion: reduce) {
    .scan-line, .scan-line-cam, .pulse-ring {
      animation: none !important;
      display: none !important;
    }
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
  }
  /* Material Symbols */
  .material-symbols-outlined {
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  }
  .material-symbols-outlined[data-weight="fill"] {
    font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  }
</style>
"""

# ── CSS overrides Gradio para integrar con el sistema de diseño ────────────────

_CSS = """
/* Base */
footer.svelte-1ax1toq, footer { display: none !important; }
.gradio-container {
  max-width: 100% !important;
  padding: 0 !important;
  background: #f7f9fb !important;
  font-family: 'Inter', sans-serif !important;
}

/* Tabs (desing/ nav style) */
.tabs > .tab-nav {
  border-bottom: 1px solid #c3c6d1 !important;
  background: white !important;
  padding: 0 40px !important;
  gap: 0 !important;
}
.tabs > .tab-nav > button {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  color: #43474f !important;
  padding: 12px 22px !important;
  border-radius: 0 !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  background: transparent !important;
  transition: color 200ms ease, border-color 200ms ease, background 200ms ease !important;
  cursor: pointer !important;
}
.tabs > .tab-nav > button:hover:not(.selected) {
  color: #001e40 !important;
  background: rgba(0,105,110,.04) !important;
}
.tabs > .tab-nav > button.selected {
  color: #00696e !important;
  border-bottom-color: #00696e !important;
}

/* Keyboard focus (WCAG AA — 4.5:1 contrast ring) */
*:focus-visible {
  outline: 2px solid #00696e !important;
  outline-offset: 2px !important;
  border-radius: 4px !important;
}

/* Cursor consistency */
button:not(:disabled), [role="button"] { cursor: pointer !important; }

/* Gradio loading state — communicate processing visually */
.generating #btn-verify button,
.generating #btn-predict button {
  opacity: 0.7 !important;
  cursor: wait !important;
  pointer-events: none !important;
}

/* Botón verificar (desing/ primary button) */
#btn-verify button {
  background: #001e40 !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  box-shadow: 0px 8px 30px rgba(0,51,102,0.2) !important;
  transition: all .3s !important;
  padding: 14px 0 !important;
  overflow: hidden !important;
}
#btn-verify button:hover {
  transform: translateY(-2px) !important;
  background: linear-gradient(135deg, #001e40, #00696e) !important;
  box-shadow: 0px 12px 35px rgba(0,105,110,.35) !important;
}

/* Botón identificar (desing/ CTA gradient) */
#btn-predict button {
  background: linear-gradient(135deg, #001e40 0%, #00696e 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  box-shadow: 0px 8px 30px rgba(0,245,255,0.2) !important;
  transition: all .3s !important;
  padding: 14px 0 !important;
}
#btn-predict button:hover:not(:disabled) {
  transform: translateY(-1px) !important;
  box-shadow: 0 12px 35px rgba(0,105,110,.35) !important;
}
#btn-predict button:disabled {
  background: #c3c6d1 !important;
  box-shadow: none !important;
  color: #43474f !important;
  opacity: 0.6 !important;
}

/* Input (desing/ input fields) */
#inp-declared input, #inp-declared textarea {
  border: 1px solid #c3c6d1 !important;
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 15px !important;
  background: white !important;
  transition: border-color .2s, box-shadow .2s !important;
  padding: 10px 14px !important;
}
#inp-declared input:focus, #inp-declared textarea:focus {
  border-color: #00696e !important;
  box-shadow: 0 0 0 3px rgba(0,105,110,.12) !important;
  outline: none !important;
}

/* Slider */
input[type="range"] { accent-color: #00696e !important; }

/* Image upload areas */
.upload-container, .image-container {
  border: 2px dashed #c3c6d1 !important;
  border-radius: 12px !important;
  background: #f7f9fb !important;
  transition: border-color .2s !important;
}
.upload-container:hover, .image-container:hover {
  border-color: #00696e !important;
}

/* Traducciones (desing/ an_lisis_y_resultados AI summary) */
#out-translations .prose h2 {
  font-family: 'Montserrat', sans-serif !important;
  font-size: 28px !important;
  font-weight: 700 !important;
  background: linear-gradient(135deg, #001e40 0%, #00696e 100%) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  margin-bottom: 4px !important;
}
#out-translations .prose h3 {
  font-family: 'Inter', sans-serif !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  color: #00696e !important;
  text-transform: uppercase !important;
  letter-spacing: .07em !important;
  margin-top: 16px !important;
}
#out-translations .prose strong {
  color: #001e40 !important;
  font-size: 15px !important;
}
#out-translations .prose hr { border-color: #e6e8ea !important; }
#out-translations .prose p {
  color: #43474f !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
}

/* Label top-k */
#out-topk .label-wrap {
  border: 1px solid #c3c6d1 !important;
  border-radius: 12px !important;
  background: white !important;
}
"""

# ── HTML blocks: adaptados de desing/ ─────────────────────────────────────────

# Header (desing/ TopNavBar pattern)
_HEADER = """
<header class="bg-surface/80 backdrop-blur-xl flex justify-between items-center px-margin-desktop w-full sticky top-0 z-50 border-b border-outline-variant/30 shadow-sm py-4">
  <div class="font-headline-md text-headline-md font-bold text-primary flex items-center gap-2">
    <span class="material-symbols-outlined text-primary" data-weight="fill">travel_explore</span>
    RutaCamba
  </div>
  <div class="flex items-center gap-2">
    <span class="inline-flex items-center gap-2 px-3 py-1 bg-[#E0FBFC] text-secondary rounded-full font-label-md text-label-md text-xs">
      <span class="w-2 h-2 rounded-full bg-green-500 inline-block animate-pulse"></span>
      Asistente Turístico · Santa Cruz de la Sierra
    </span>
  </div>
</header>
"""

# Tab 1 — Verificación (adaptado de inicio_y_autenticaci_n_facial)
_AUTH_HERO = """
<div class="hidden md:flex flex-col justify-end h-full min-h-[400px] relative overflow-hidden rounded-xl"
     style="background: linear-gradient(135deg, #001e40 0%, #003366 50%, #00696e 100%);">
  <div class="absolute inset-0 opacity-10"
       style="background-image: radial-gradient(circle at 30% 70%, #00dce5 0%, transparent 50%), radial-gradient(circle at 80% 20%, #a7c8ff 0%, transparent 40%);"></div>
  <div class="glass-overlay rounded-xl p-6 m-4 relative z-10">
    <h2 class="font-headline-lg text-headline-md font-bold text-white mb-2">RutaCamba</h2>
    <p class="font-body-md text-body-md text-white/80">
      Identificación inteligente de landmarks de Santa Cruz de la Sierra.<br>
      Acceso exclusivo para usuarios verificados.
    </p>
    <div class="flex gap-2 mt-4 flex-wrap">
      <span class="px-3 py-1 bg-white/10 text-white rounded-full font-caption text-caption border border-white/20">CNN Transfer Learning</span>
      <span class="px-3 py-1 bg-white/10 text-white rounded-full font-caption text-caption border border-white/20">Re-ID Biométrico</span>
      <span class="px-3 py-1 bg-white/10 text-white rounded-full font-caption text-caption border border-white/20">4 Idiomas</span>
    </div>
  </div>
</div>
"""

_AUTH_HEADING = """
<div class="space-y-4 text-center mb-6">
  <h1 class="font-display-lg text-headline-lg font-bold text-primary tracking-tight">
    Bienvenido a la <span class="text-secondary">nueva era</span><br>del turismo inteligente
  </h1>
  <p class="font-body-lg text-body-md text-on-surface-variant max-w-sm mx-auto">
    Verificá tu identidad con reconocimiento facial para acceder al asistente.
  </p>
</div>
"""

_FACE_SCANNER = """
<div class="flex flex-col items-center my-4">
  <!-- Scanner animado (desing/ inicio_y_autenticaci_n_facial) -->
  <div class="relative w-36 h-36 group">
    <!-- Anillo exterior decorativo -->
    <div class="absolute inset-0 rounded-full border border-outline-variant/50"></div>
    <div class="absolute inset-2 rounded-full border-2 border-dashed border-primary-fixed-dim/30"
         style="animation: spin 20s linear infinite;"></div>
    <!-- Área del scanner -->
    <div class="absolute inset-4 rounded-full bg-surface-container shadow-inner overflow-hidden
                flex items-center justify-center border-2 border-transparent transition-colors duration-300
                hover:border-secondary">
      <span class="material-symbols-outlined text-6xl text-surface-tint opacity-50" data-weight="fill">face</span>
      <div class="scan-line"></div>
    </div>
    <!-- Pulse ring -->
    <div class="pulse-ring"></div>
    <!-- Corner markers -->
    <div class="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-primary"></div>
    <div class="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-primary"></div>
    <div class="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-primary"></div>
    <div class="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-primary"></div>
  </div>
  <p class="font-caption text-caption text-on-surface-variant mt-2">Sistema Re-ID activo</p>
</div>
"""

_VERIFY_SEPARATOR = """
<div class="flex items-center gap-3 my-4">
  <div class="flex-1 h-px bg-outline-variant/30"></div>
  <span class="font-caption text-caption text-outline">o subí tu selfie abajo</span>
  <div class="flex-1 h-px bg-outline-variant/30"></div>
</div>
"""

# Tab 2 — Scanner + Resultados (adaptado de esc_ner_del_entorno + an_lisis_y_resultados)
_SCAN_HEADER = """
<div class="mb-4">
  <div class="inline-flex items-center gap-2 px-3 py-1 bg-[#E0FBFC] text-secondary rounded-full font-label-md text-label-md mb-3 shadow-sm">
    <span class="material-symbols-outlined text-base">center_focus_strong</span>
    Escáner de Landmark
  </div>
  <p class="font-body-md text-body-md text-on-surface-variant">
    Subí una foto del lugar que querés identificar. El modelo CNN analizará la imagen.
  </p>
</div>
"""

_RESULTS_PLACEHOLDER = """
<div id="results-placeholder"
     class="bg-surface-container-lowest rounded-xl shadow-md border border-surface-container-highest p-6 relative overflow-hidden min-h-48 flex flex-col items-center justify-center gap-3">
  <div class="absolute top-0 right-0 w-32 h-32 bg-secondary/10 rounded-full blur-3xl -mr-10 -mt-10"></div>
  <span class="material-symbols-outlined text-5xl text-surface-tint opacity-40">image_search</span>
  <p class="font-body-md text-body-md text-on-surface-variant text-center">
    El análisis aparecerá aquí.<br>
    <span class="font-label-md text-label-md text-secondary">Identificá un lugar para comenzar.</span>
  </p>
</div>
"""

_CONFIDENCE_STATS_TEMPLATE = """
<div class="grid grid-cols-2 gap-4 mb-4">
  <div class="bg-surface-container-lowest p-4 rounded-xl shadow-sm border border-surface-container-highest">
    <div class="flex items-center gap-2 mb-2 text-secondary">
      <span class="material-symbols-outlined text-xl">psychology</span>
      <span class="font-label-md text-label-md">Confianza IA</span>
    </div>
    <div class="font-headline-md text-headline-md text-primary" id="conf-value">—</div>
  </div>
  <div class="bg-surface-container-lowest p-4 rounded-xl shadow-sm border border-surface-container-highest">
    <div class="flex items-center gap-2 mb-2 text-surface-tint">
      <span class="material-symbols-outlined text-xl">location_on</span>
      <span class="font-label-md text-label-md">Landmark</span>
    </div>
    <div class="font-body-md text-body-md text-on-surface font-semibold text-sm" id="landmark-value">—</div>
  </div>
</div>
"""


# ── Status HTML (SVG icons, no emoji) ─────────────────────────────────────────

_STATUS_CFG = {
    "success": ("#f0fdf4", "#15803d", "#bbf7d0",
                '<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"/>'),
    "error":   ("#fef2f2", "#dc2626", "#fecaca",
                '<path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"/>'),
    "warning": ("#fffbeb", "#b45309", "#fde68a",
                '<path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke-linecap="round" stroke-linejoin="round"/>'),
    "info":    ("#eff6ff", "#2563eb", "#bfdbfe",
                '<path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"/>'),
}


def _status_html(msg: str, kind: str) -> str:
    bg, color, border, path = _STATUS_CFG[kind]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" '
        f'viewBox="0 0 24 24" stroke="{color}" stroke-width="2">{path}</svg>'
    )
    return (
        f'<div style="background:{bg};border:1px solid {border};border-radius:10px;'
        f'padding:13px 16px;display:flex;align-items:flex-start;gap:10px;'
        f'font-family:Inter,sans-serif;font-size:14px;line-height:1.55;margin-top:8px;">'
        f'<span style="flex-shrink:0;margin-top:1px;">{svg}</span>'
        f'<span style="color:{color};">{msg}</span></div>'
    )


# ── Funciones que llaman a la API ─────────────────────────────────────────────

def step_verify(declared_id: str, selfie_path: str):
    """Llama a POST /verify. Devuelve (html_status, token, estado del botón predict)."""
    if not declared_id.strip():
        return _status_html("Ingresá tu nombre de identidad.", "warning"), "", gr.update(interactive=False)
    if selfie_path is None:
        return _status_html("Subí una selfie.", "warning"), "", gr.update(interactive=False)

    try:
        with open(selfie_path, "rb") as f:
            response = requests.post(
                f"{API_URL}/verify",
                data={"declared_id": declared_id.strip()},
                files={"selfie": f},
                timeout=30,
            )
    except requests.ConnectionError:
        return (
            _status_html("No se puede conectar a la API. ¿Está corriendo en localhost:8000?", "error"),
            "",
            gr.update(interactive=False),
        )

    if response.status_code == 200:
        token = response.json()["token"]
        return (
            _status_html(
                f"Acceso concedido — Bienvenido, <strong>{declared_id}</strong>. Pasá al Paso 2.",
                "success",
            ),
            token,
            gr.update(interactive=True),
        )
    else:
        detail = response.json().get("detail", {})
        top1 = detail.get("top1_identity", "desconocido") if isinstance(detail, dict) else detail
        return (
            _status_html(
                f"Acceso denegado. Rostro más cercano en galería: <strong>{top1}</strong>.",
                "error",
            ),
            "",
            gr.update(interactive=False),
        )


_LANG_INFO: dict[str, tuple[str, str]] = {
    "es": ("🇧🇴", "Español"),
    "en": ("🇺🇸", "English"),
    "fr": ("🇫🇷", "Français"),
    "it": ("🇮🇹", "Italiano"),
}


def _format_translations(landmark_id: str, translations: dict) -> str:
    """Formatea traducciones como el AI summary card de an_lisis_y_resultados."""
    title = landmark_id.replace("_", " ").title()
    parts = [f"## {title}\n"]
    for lang_code, (flag, lang_label) in _LANG_INFO.items():
        data = translations.get(lang_code, {})
        if isinstance(data, dict) and data:
            nombre = data.get("nombre", "—")
            descripcion = data.get("descripcion", "—")
            parts.append(
                f"### {flag} {lang_label}\n\n"
                f"**{nombre}**\n\n"
                f"{descripcion}"
            )
        else:
            parts.append(f"### {flag} {lang_label}\n\n—")
    return "\n\n---\n\n".join(parts)


def step_predict(token: str, image_path: str, k: int):
    """Llama a POST /predict. Devuelve (dict para gr.Label, markdown de traducciones)."""
    if not token:
        return {}, "Primero verificá tu identidad en el Paso 1."
    if image_path is None:
        return {}, "Subí una foto del lugar."

    try:
        with open(image_path, "rb") as f:
            response = requests.post(
                f"{API_URL}/predict",
                data={"token": token, "k": int(k)},
                files={"image": f},
                timeout=30,
            )
    except requests.ConnectionError:
        return {}, "No se puede conectar a la API."

    if response.status_code == 200:
        data = response.json()
        top_k_dict = {item[0]: float(item[1]) for item in data["top_k"]}
        info = _format_translations(data["landmark_id"], data["translations"])
        return top_k_dict, info
    elif response.status_code == 401:
        return {}, "Sesión expirada. Volvé a verificar tu identidad."
    else:
        detail = response.json().get("detail", "Error desconocido.")
        return {}, f"Error: {detail}"


# ── Interfaz ──────────────────────────────────────────────────────────────────

with gr.Blocks(title="RutaCamba — Asistente Turístico") as demo:
    token_state = gr.State("")

    # ── Header: TopNavBar (desing/) ────────────────────────────────────────────
    gr.HTML(_HEADER)

    with gr.Tabs():

        # ── Tab 1: Verificación (desing/ inicio_y_autenticaci_n_facial) ───────
        with gr.Tab("① Verificar identidad"):
            with gr.Row(equal_height=True):
                # Panel izquierdo — hero (solo desktop)
                with gr.Column(scale=1):
                    gr.HTML(_AUTH_HERO)

                # Panel derecho — formulario de auth
                with gr.Column(scale=1):
                    gr.HTML(_AUTH_HEADING)
                    gr.HTML(_FACE_SCANNER)
                    gr.HTML(_VERIFY_SEPARATOR)

                    declared_id_box = gr.Textbox(
                        label="Identidad declarada",
                        placeholder="ej: maria_lopez",
                        elem_id="inp-declared",
                    )
                    selfie_input = gr.Image(
                        type="filepath",
                        label="Selfie",
                        elem_id="img-selfie",
                    )
                    verify_btn = gr.Button(
                        "Verificar identidad",
                        variant="primary",
                        elem_id="btn-verify",
                    )
                    verify_status = gr.HTML(elem_id="out-status")

        # ── Tab 2: Escáner + Resultados (desing/ esc_ner_del_entorno + an_lisis) ─
        with gr.Tab("② Identificar lugar"):
            with gr.Row(equal_height=False):
                # Columna izquierda — cámara (desing/ esc_ner_del_entorno)
                with gr.Column(scale=1):
                    gr.HTML(_SCAN_HEADER)

                    # Scanner frame sobre el upload de imagen
                    with gr.Group(elem_classes=["scanner-frame"]):
                        gr.HTML("""<div></div>
                        <div class="scan-line-cam" style="pointer-events:none;z-index:5;"></div>""")
                        place_image = gr.Image(
                            type="filepath",
                            label="",
                            elem_id="img-place",
                        )

                    k_slider = gr.Slider(
                        minimum=1, maximum=8, value=3, step=1,
                        label="Resultados top-k",
                    )
                    predict_btn = gr.Button(
                        "Identificar lugar",
                        variant="primary",
                        interactive=False,
                        elem_id="btn-predict",
                    )

                # Columna derecha — resultados (desing/ an_lisis_y_resultados)
                with gr.Column(scale=2):
                    gr.HTML("""
                    <div class="mb-4">
                      <div class="inline-flex items-center gap-2 px-3 py-1 bg-[#E0FBFC] text-secondary rounded-full font-label-md text-label-md text-xs mb-3 shadow-sm">
                        <span class="material-symbols-outlined text-base">verified_user</span>
                        Análisis de IA
                      </div>
                    </div>
                    """)

                    # Bento stats (desing/ an_lisis_y_resultados pequeñas cards)
                    label_output = gr.Label(
                        label="Clasificación CNN (top-k + probabilidades)",
                        elem_id="out-topk",
                    )

                    # AI summary card (desing/ an_lisis_y_resultados Resumen Inteligente)
                    gr.HTML("""
                    <div class="bg-surface-container-lowest rounded-xl shadow-md border border-surface-container-highest p-1 relative overflow-hidden mt-4">
                      <div class="absolute top-0 right-0 w-32 h-32 bg-secondary/10 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none"></div>
                      <div class="flex items-center gap-2 px-4 pt-4 pb-2">
                        <span class="material-symbols-outlined text-secondary" data-weight="fill">auto_awesome</span>
                        <span class="font-headline-md text-base font-semibold text-primary" style="font-family:Montserrat,sans-serif;">Resumen multilingüe</span>
                      </div>
                    </div>
                    """)
                    translations_output = gr.Markdown(
                        elem_id="out-translations",
                        container=False,
                    )

    # ── Eventos ────────────────────────────────────────────────────────────────
    verify_btn.click(
        fn=step_verify,
        inputs=[declared_id_box, selfie_input],
        outputs=[verify_status, token_state, predict_btn],
    )

    predict_btn.click(
        fn=step_predict,
        inputs=[token_state, place_image, k_slider],
        outputs=[label_output, translations_output],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("UI_PORT", 7860)),
        css=_CSS,
        head=_HEAD,
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.blue,
            secondary_hue=gr.themes.colors.teal,
            neutral_hue=gr.themes.colors.slate,
            font=[gr.themes.GoogleFont("Inter"), "sans-serif"],
        ),
    )
