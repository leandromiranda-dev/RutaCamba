"""ui/app.py — Interfaz Gradio de RutaCamba (Nicole, Fase 6).

Flujo de dos pasos:
    1. El usuario declara su identidad y sube una selfie → /verify
    2. Si el acceso fue concedido, sube una foto del lugar → /predict

La UI consume la API con requests y NUNCA carga modelos directamente.
Ejecutar con: python ui/app.py  (requiere que la API esté corriendo en :8000)
"""
import os

import gradio as gr
import requests

API_URL = os.environ.get("API_URL", "http://localhost:8000")


# ── Funciones que llaman a la API ─────────────────────────────────────────────

def step_verify(declared_id: str, selfie_path: str):
    """Llama a POST /verify. Devuelve (mensaje, token, estado del botón predict)."""
    if not declared_id.strip():
        return "Por favor ingresá tu nombre de identidad.", "", gr.update(interactive=False)
    if selfie_path is None:
        return "Por favor subí una selfie.", "", gr.update(interactive=False)

    try:
        with open(selfie_path, "rb") as f:
            response = requests.post(
                f"{API_URL}/verify",
                data={"declared_id": declared_id.strip()},
                files={"selfie": f},
                timeout=30,
            )
    except requests.ConnectionError:
        return "No se puede conectar a la API. ¿Está corriendo en localhost:8000?", "", gr.update(interactive=False)

    if response.status_code == 200:
        token = response.json()["token"]
        return (
            f"Acceso concedido para **{declared_id}**. Ahora podés identificar un lugar.",
            token,
            gr.update(interactive=True),
        )
    else:
        detail = response.json().get("detail", {})
        top1 = detail.get("top1_identity", "desconocido") if isinstance(detail, dict) else detail
        return (
            f"Acceso denegado. El rostro más cercano en la galería es **{top1}**.",
            "",
            gr.update(interactive=False),
        )


def _format_translations(landmark_id: str, translations: dict) -> str:
    """Formatea la info multilingüe del landmark como markdown."""
    title = landmark_id.replace("_", " ").title()
    lang_labels = {
        "es": "Espanol",
        "en": "English",
        "fr": "Francais",
        "it": "Italiano",
    }
    sections = [f"## {title}\n"]
    for lang_code, lang_label in lang_labels.items():
        data = translations.get(lang_code, {})
        if isinstance(data, dict) and data:
            nombre = data.get("nombre", "—")
            descripcion = data.get("descripcion", "—")
            sections.append(f"### {lang_label}\n\n**{nombre}**\n\n{descripcion}")
        else:
            sections.append(f"### {lang_label}\n\n—")
    return "\n\n---\n\n".join(sections)


def step_predict(token: str, image_path: str, k: int):
    """Llama a POST /predict. Devuelve (dict para gr.Label, markdown de traducciones)."""
    if not token:
        return {}, "Primero verificá tu identidad en el paso 1."
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

with gr.Blocks(title="RutaCamba — Asistente turístico") as demo:
    token_state = gr.State("")

    gr.Markdown(
        "# RutaCamba\n"
        "**Asistente turístico inteligente para Santa Cruz de la Sierra, Bolivia.**\n\n"
        "Primero verificá tu identidad, luego identificá el lugar que querés conocer."
    )

    with gr.Tab("Paso 1 — Verificación de identidad"):
        gr.Markdown("Ingresá tu nombre y subí una selfie para que el sistema te reconozca.")
        with gr.Row():
            declared_id_box = gr.Textbox(label="Tu nombre (identidad declarada)", placeholder="ej: maria_lopez")
            selfie_input = gr.Image(type="filepath", label="Selfie")
        verify_btn = gr.Button("Verificar identidad", variant="primary")
        verify_status = gr.Markdown()

    with gr.Tab("Paso 2 — Identificar lugar"):
        gr.Markdown("Subí una foto del lugar que querés identificar.")
        with gr.Row():
            place_image = gr.Image(type="filepath", label="Foto del lugar")
            k_slider = gr.Slider(minimum=1, maximum=8, value=3, step=1, label="Resultados top-k")
        predict_btn = gr.Button("Identificar", variant="primary", interactive=False)
        with gr.Row():
            label_output = gr.Label(label="Clasificación (top-k)")
            translations_output = gr.Markdown(label="Información del lugar")

    # ── Eventos ───────────────────────────────────────────────────────────────
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
        show_api=False,
    )
