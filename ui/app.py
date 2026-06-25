"""ui/app.py — RutaCamba — Validación facial → Chat turístico WhatsApp-azul."""
import base64
import os
import re
from datetime import datetime

import gradio as gr
import requests

API_URL = os.environ.get("API_URL", "http://localhost:8000")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _img_b64(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = path.rsplit(".", 1)[-1].lower()
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")
    return f"data:image/{mime};base64,{data}"


def _md(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"_(.*?)_", r"<em>\1</em>", text)
    text = text.replace("\n\n", "<br><br>").replace("\n", "<br>")
    return text


# ── Chat renderer ──────────────────────────────────────────────────────────────

def render_chat(history: list) -> str:
    if not history:
        return (
            '<div style="display:flex;flex-direction:column;align-items:center;'
            'justify-content:center;padding:60px 24px;background:#E8EFFF;height:100%;">'
            '<div style="font-size:60px;margin-bottom:16px;opacity:.35;">💬</div>'
            '<p style="font-family:DM Sans,sans-serif;font-size:15px;color:#8A99BB;'
            'text-align:center;margin:0;line-height:1.6;">'
            'Tu conversación aparecerá aquí</p></div>'
        )

    _AVATAR = (
        '<div style="width:30px;height:30px;border-radius:50%;flex-shrink:0;'
        'background:linear-gradient(135deg,#1565C0 0%,#42A5F5 100%);'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:15px;align-self:flex-end;">🤖</div>'
    )

    ts = datetime.now().strftime("%H:%M")
    parts: list[str] = [
        f'<div style="text-align:center;margin:14px 0;">'
        f'<span style="font-family:DM Sans,sans-serif;font-size:11px;color:#90A4C0;'
        f'background:#D8E4F8;padding:4px 14px;border-radius:20px;">Hoy {ts}</span>'
        f'</div>'
    ]

    for msg in history:
        if msg["role"] == "ai":
            parts.append(
                '<div style="display:flex;align-items:flex-end;gap:8px;'
                'margin-bottom:8px;margin-right:15%;">'
                + _AVATAR
                + '<div style="background:#FFFFFF;border-radius:18px 18px 18px 4px;'
                'padding:11px 15px;box-shadow:0 1px 3px rgba(21,101,192,.1);'
                'font-family:DM Sans,sans-serif;font-size:14px;color:#1A2340;'
                f'line-height:1.6;">{_md(msg.get("text",""))}</div></div>'
            )
        else:
            inner = ""
            if msg.get("image"):
                try:
                    src = _img_b64(msg["image"])
                    inner += (
                        f'<img src="{src}" alt="foto adjunta" '
                        'style="max-width:220px;max-height:220px;object-fit:cover;'
                        'border-radius:12px;display:block;margin-bottom:6px;">'
                    )
                except Exception:
                    inner += '<em style="opacity:.75">[imagen adjunta]</em><br>'
            if msg.get("text"):
                inner += msg["text"]
            parts.append(
                '<div style="display:flex;justify-content:flex-end;'
                'margin-bottom:8px;margin-left:15%;">'
                '<div style="background:#1565C0;border-radius:18px 18px 4px 18px;'
                'padding:11px 15px;font-family:DM Sans,sans-serif;font-size:14px;'
                f'color:#FFFFFF;line-height:1.6;">{inner}</div></div>'
            )

    # Auto-scroll to bottom of the messages container
    parts.append(
        '<script>'
        'setTimeout(function(){'
        'var d=document.getElementById("chat-display");'
        'if(d){d.scrollTop=d.scrollHeight;}'
        '},60);'
        '</script>'
    )

    return (
        '<div id="rc-msgs" style="padding:8px 14px 20px;background:#E8EFFF;">'
        + "".join(parts)
        + '</div>'
    )


# ── API wrappers ───────────────────────────────────────────────────────────────

def _call_verify(name: str, selfie_path: str) -> requests.Response:
    with open(selfie_path, "rb") as f:
        return requests.post(
            f"{API_URL}/verify",
            data={"declared_id": name.strip()},
            files={"selfie": f},
            timeout=30,
        )


def _call_predict(token: str, img_path: str, k: int = 3) -> requests.Response:
    with open(img_path, "rb") as f:
        return requests.post(
            f"{API_URL}/predict",
            data={"token": token, "k": k},
            files={"image": f},
            timeout=30,
        )


# ── Event handlers ─────────────────────────────────────────────────────────────

def verify_fn(name: str, selfie_path: str):
    def _err(msg):
        return msg, "", gr.update(), gr.update(), render_chat([]), []

    if not name.strip():
        return _err("⚠️ Escribí tu nombre primero.")
    if selfie_path is None:
        return _err("⚠️ Adjuntá una foto de tu cara o usá la cámara.")

    try:
        resp = _call_verify(name, selfie_path)
    except requests.ConnectionError:
        return _err("🔴 Sin conexión a la API. ¿Está corriendo el servidor?")

    if resp.status_code == 200:
        token = resp.json()["token"]
        greeting = (
            f"¡Hola, **{name.strip()}**! 👋 Soy tu guía turístico de **RutaCamba**.\n\n"
            "Mandame una foto de cualquier lugar de **Santa Cruz de la Sierra** "
            "y te cuento todo sobre él. 📸\n\n"
            "Usá el botón 📎 para adjuntar una imagen."
        )
        history = [{"role": "ai", "text": greeting, "image": None}]
        return (
            "",
            token,
            gr.update(visible=False),
            gr.update(visible=True),
            render_chat(history),
            history,
        )

    detail = resp.json().get("detail", {})
    top1 = detail.get("top1_identity", "desconocido") if isinstance(detail, dict) else str(detail)
    return _err(f"❌ No verificado — el rostro más parecido es **{top1}**. Intentá con otra foto.")


def toggle_attach(img_vis: bool):
    return gr.update(visible=not img_vis), not img_vis


def send_fn(token: str, text: str, img_path, history: list, img_vis: bool):
    if not token:
        return render_chat(history), history, "", None, img_vis

    has_img = img_path is not None
    has_txt = bool(text.strip())
    if not has_img and not has_txt:
        return render_chat(history), history, "", None, img_vis

    user_msg = {
        "role": "user",
        "text": text.strip() if has_txt else "",
        "image": img_path,
    }
    history = history + [user_msg]

    if has_img:
        try:
            resp = _call_predict(token, img_path)
        except requests.ConnectionError:
            ai_msg = {"role": "ai", "text": "🔴 Sin conexión a la API.", "image": None}
            return render_chat(history + [ai_msg]), history + [ai_msg], "", None, False

        if resp.status_code == 200:
            data = resp.json()
            top_k = data["top_k"]
            trans = data["translations"]
            es = trans.get("es", {})
            en = trans.get("en", {})
            nombre = es.get("nombre", data["landmark_id"].replace("_", " ").title())
            nombre_en = en.get("nombre", "")
            desc = es.get("descripcion", "")
            conf = int(float(top_k[0][1]) * 100) if top_k else 0
            otros = [
                f"• {n.replace('_',' ').title()} ({int(float(s)*100)}%)"
                for n, s in top_k[1:3]
            ]
            ai_text = (
                f"📍 **{nombre}**"
                + (f"\n_{nombre_en}_" if nombre_en else "")
                + f"\n\nConfianza: **{conf}%**\n\n{desc}"
                + ("\n\n**Otras posibilidades:**\n" + "\n".join(otros) if otros else "")
            )
        elif resp.status_code == 401:
            ai_text = "⚠️ Sesión expirada. Recargá la página para verificarte de nuevo."
        else:
            ai_text = f"🔴 Error: {resp.json().get('detail', 'Error desconocido.')}"

        ai_msg = {"role": "ai", "text": ai_text, "image": None}
        new_hist = history + [ai_msg]
        return (
            render_chat(new_hist), new_hist, "",
            gr.update(value=None, visible=False), False,
        )

    # Mensaje de texto solo
    ai_msg = {
        "role": "ai",
        "text": "Para identificar un lugar adjuntá una foto 📷\nUsá el botón **📎** para subir una imagen.",
        "image": None,
    }
    new_hist = history + [ai_msg]
    return render_chat(new_hist), new_hist, "", gr.update(), img_vis


# ── HTML ───────────────────────────────────────────────────────────────────────

_HEAD = """
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&family=Montserrat:wght@700;800&display=swap" rel="stylesheet"/>
"""

_AUTH_HERO = """
<div style="
  background: linear-gradient(155deg, #0D47A1 0%, #1565C0 50%, #0A3D8F 100%);
  padding: 44px 24px 52px;
  text-align: center;
  position: relative;
  overflow: hidden;
">
  <div style="position:absolute;top:-50px;right:-50px;width:180px;height:180px;
              border-radius:50%;background:rgba(255,255,255,.06);pointer-events:none;"></div>
  <div style="position:absolute;bottom:-70px;left:-35px;width:220px;height:220px;
              border-radius:50%;background:rgba(66,165,245,.09);pointer-events:none;"></div>
  <div style="position:relative;z-index:1;">
    <div style="width:68px;height:68px;border-radius:50%;
                background:rgba(255,255,255,.18);backdrop-filter:blur(6px);
                margin:0 auto 18px;display:flex;align-items:center;
                justify-content:center;font-size:32px;
                box-shadow:0 4px 20px rgba(0,0,0,.2);">🗺️</div>
    <h1 style="font-family:Montserrat,sans-serif;font-size:30px;font-weight:800;
               color:#fff;margin:0 0 10px;letter-spacing:-.02em;">RutaCamba</h1>
    <p style="font-family:DM Sans,sans-serif;font-size:15px;
              color:rgba(255,255,255,.78);margin:0 auto;max-width:290px;line-height:1.6;">
      Tu guía turístico inteligente para Santa Cruz de la Sierra
    </p>
  </div>
</div>
"""

_AUTH_INSTRUCTIONS = """
<div style="max-width:440px;margin:0 auto;padding:14px 24px 0;text-align:center;">
  <div style="display:inline-flex;align-items:center;gap:8px;background:#DDEAFF;
              border-radius:20px;padding:5px 14px;margin-bottom:8px;">
    <span style="width:7px;height:7px;border-radius:50%;background:#1565C0;
                 display:inline-block;"></span>
    <span style="font-family:DM Sans,sans-serif;font-size:12px;font-weight:700;
                 color:#1565C0;">Paso 1 — Verificación</span>
  </div>
  <h2 style="font-family:Montserrat,sans-serif;font-size:19px;font-weight:800;
             color:#0D1A33;margin:0 0 5px;">Verificá tu identidad</h2>
  <p style="font-family:DM Sans,sans-serif;font-size:13px;color:#5A6A8A;
            margin:0 auto;max-width:300px;line-height:1.45;">
    Subí una foto de tu cara <strong style="color:#0D1A33;">o abrí la cámara</strong>.
    Si la verificación pasa, entrás al chat turístico.
  </p>
</div>
"""

_AUTH_SPACER = '<div style="height:6px;"></div>'

_AUTH_BOTTOM_SPACER = '<div style="height:20px;"></div>'

_CHAT_HEADER = """
<div style="
  background: #1565C0;
  padding: 0 16px;
  height: 62px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
">
  <div style="width:42px;height:42px;border-radius:50%;
              background:rgba(255,255,255,.18);
              display:flex;align-items:center;justify-content:center;font-size:21px;">🤖</div>
  <div>
    <div style="font-family:DM Sans,sans-serif;font-size:16px;font-weight:700;
                color:#fff;line-height:1.2;">RutaCamba AI</div>
    <div style="font-family:DM Sans,sans-serif;font-size:12px;
                color:rgba(255,255,255,.72);">en línea</div>
  </div>
</div>
"""

# ── CSS ────────────────────────────────────────────────────────────────────────

_CSS = """
/* ── Reset global ── */
footer, footer.svelte-1ax1toq { display: none !important; }
.gradio-container {
  max-width: 100% !important;
  padding: 0 !important;
  margin: 0 !important;
  font-family: 'DM Sans', sans-serif !important;
  background: transparent !important;
}

/* ── AUTH SCREEN ── */
#auth-screen {
  min-height: 100vh;
  background: #F0F5FF;
}
#auth-screen > *, #auth-screen > * > * {
  padding: 0 !important;
  gap: 0 !important;
}

/* Selfie upload */
#selfie-upload {
  max-width: 440px !important;
  margin: 0 auto !important;
  padding: 0 24px !important;
}
#selfie-upload .upload-container {
  border: 2px dashed #1565C0 !important;
  border-radius: 16px !important;
  background: #F4F8FF !important;
  min-height: 170px !important;
  transition: border-color .2s, background .2s !important;
}
#selfie-upload .upload-container:hover {
  border-color: #0D47A1 !important;
  background: #EAF0FF !important;
}

/* Name input */
#name-inp {
  max-width: 440px !important;
  margin: 0 auto !important;
  padding: 0 24px !important;
}
#name-inp label > span { display: none !important; }
#name-inp input {
  border: 1.5px solid #BDD0F0 !important;
  border-radius: 12px !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 15px !important;
  padding: 14px 16px !important;
  background: #fff !important;
  color: #0D1A33 !important;
  transition: border-color .2s, box-shadow .2s !important;
}
#name-inp input:focus {
  border-color: #1565C0 !important;
  box-shadow: 0 0 0 3px rgba(21,101,192,.14) !important;
  outline: none !important;
}

/* Verify button — gr.Button puts elem_id directly on <button> */
#verify-btn {
  background: #1565C0 !important;
  color: #fff !important;
  border: none !important;
  border-radius: 12px !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 700 !important;
  font-size: 16px !important;
  padding: 16px 0 !important;
  width: calc(100% - 48px) !important;
  max-width: 392px !important;
  margin: 8px auto 0 !important;
  display: flex !important;
  justify-content: center !important;
  box-shadow: 0 4px 18px rgba(21,101,192,.32) !important;
  transition: background .2s, transform .1s, box-shadow .2s !important;
}
#verify-btn:hover {
  background: #0D47A1 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 8px 24px rgba(21,101,192,.38) !important;
}
#verify-btn:active { transform: none !important; }

/* Verify status */
#verify-msg {
  max-width: 440px !important;
  margin: 0 auto !important;
  padding: 4px 24px 0 !important;
  text-align: center !important;
}
#verify-msg .prose p {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
  color: #111111 !important;
  text-align: center !important;
  margin: 0 !important;
}

/* ══ CHAT SCREEN ══
   Use position:fixed overlay so height is exactly 100vh,
   independent of Gradio's outer container padding/margins.
   Children are positioned absolutely within this fixed frame.
*/
#chat-screen {
  position: fixed !important;
  inset: 0 !important;
  z-index: 100 !important;
  background: #E8EFFF !important;
  overflow: hidden !important;
}
/* Reset Gradio wrapper padding on all children */
#chat-screen > * {
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
  box-shadow: none !important;
  max-width: 100% !important;
  width: 100% !important;
}

/* ── Chat header: top 62px ── */
#chat-screen > .block:first-child {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  height: 62px !important;
  z-index: 10 !important;
  padding: 0 !important;
}
#chat-screen > .block:first-child .wrap { position: relative !important; }
#chat-screen > .block:first-child .html-container { height: 62px !important; overflow: hidden !important; }

/* ── Messages: fills space between header (62px) and input bar (74px) ── */
#chat-display {
  position: absolute !important;
  top: 62px !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 74px !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  background: #E8EFFF !important;
  padding: 0 !important;
}
#chat-display .wrap { position: relative !important; }
#chat-display .html-container {
  height: auto !important;
  min-height: 100% !important;
  overflow: visible !important;
  background: #E8EFFF !important;
}

/* ── Attach image: overlays above input bar when visible ── */
#chat-attach {
  position: absolute !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 74px !important;
  z-index: 8 !important;
  background: #fff !important;
  border-top: 1px solid #D0DCF4 !important;
  padding: 8px 16px !important;
}
#chat-attach .wrap { position: relative !important; }
#chat-attach .upload-container {
  border: 1.5px dashed #1565C0 !important;
  border-radius: 10px !important;
  background: #F4F8FF !important;
  min-height: 90px !important;
}

/* ── Input bar: bottom 74px ── */
#input-bar {
  position: absolute !important;
  bottom: 0 !important;
  left: 0 !important;
  right: 0 !important;
  height: 74px !important;
  z-index: 10 !important;
  background: #EEF4FF !important;
  border-top: 1px solid #D0DCF4 !important;
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  padding: 10px 12px !important;
  gap: 8px !important;
  box-sizing: border-box !important;
}
#input-bar > * { padding: 0 !important; margin: 0 !important; }

/* Attach button — elem_id is directly on <button> */
#attach-btn {
  background: #DDEAFF !important;
  color: #1565C0 !important;
  border: none !important;
  border-radius: 50% !important;
  width: 44px !important;
  height: 44px !important;
  min-width: 44px !important;
  font-size: 20px !important;
  padding: 0 !important;
  flex-shrink: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: background .18s !important;
}
#attach-btn:hover { background: #C8DAFF !important; }

/* Message textarea */
#msg-inp { flex: 1 !important; min-width: 0 !important; }
#msg-inp label { display: none !important; }
#msg-inp .block, #msg-inp .wrap { padding: 0 !important; }
#msg-inp textarea {
  border: 1.5px solid #BDD0F0 !important;
  border-radius: 22px !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 15px !important;
  padding: 10px 16px !important;
  background: #fff !important;
  resize: none !important;
  line-height: 1.45 !important;
  overflow-y: auto !important;
  transition: border-color .2s !important;
  width: 100% !important;
  box-sizing: border-box !important;
}
#msg-inp textarea:focus {
  border-color: #1565C0 !important;
  outline: none !important;
  box-shadow: 0 0 0 2px rgba(21,101,192,.12) !important;
}

/* Send button — elem_id is directly on <button> */
#send-btn {
  background: #1565C0 !important;
  color: #fff !important;
  border: none !important;
  border-radius: 50% !important;
  width: 44px !important;
  height: 44px !important;
  min-width: 44px !important;
  font-size: 20px !important;
  padding: 0 !important;
  flex-shrink: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: 0 2px 8px rgba(21,101,192,.32) !important;
  transition: background .18s, transform .1s !important;
}
#send-btn:hover {
  background: #0D47A1 !important;
  transform: scale(1.06) !important;
}

/* ── Mobile ── */
@media (max-width: 480px) {
  #selfie-upload, #name-inp, #verify-btn, #verify-msg {
    padding-left: 16px !important;
    padding-right: 16px !important;
  }
}
"""

# ── Layout ─────────────────────────────────────────────────────────────────────

with gr.Blocks(title="RutaCamba — Asistente Turístico") as demo:
    token_state = gr.State("")
    chat_hist = gr.State([])
    img_vis = gr.State(False)

    # ── PANTALLA 1: Verificación facial ────────────────────────────────────────
    with gr.Column(elem_id="auth-screen") as auth_col:
        gr.HTML(_AUTH_HERO)
        gr.HTML(_AUTH_INSTRUCTIONS)
        gr.HTML(_AUTH_SPACER)

        selfie = gr.Image(
            sources=["webcam", "upload"],
            type="filepath",
            label="Foto de tu cara",
            show_label=False,
            elem_id="selfie-upload",
        )
        gr.HTML(_AUTH_SPACER)

        name_inp = gr.Textbox(
            placeholder="Tu nombre o usuario (ej: maria_lopez)",
            show_label=False,
            elem_id="name-inp",
        )
        gr.HTML(_AUTH_SPACER)

        verify_btn = gr.Button("✓  Verificar identidad", elem_id="verify-btn")
        verify_msg = gr.Markdown(elem_id="verify-msg")
        gr.HTML(_AUTH_BOTTOM_SPACER)

    # ── PANTALLA 2: Chat WhatsApp-azul ─────────────────────────────────────────
    with gr.Column(elem_id="chat-screen", visible=False) as chat_col:
        gr.HTML(_CHAT_HEADER)

        chat_disp = gr.HTML(
            value=render_chat([]),
            elem_id="chat-display",
        )

        attach_img = gr.Image(
            sources=["upload", "webcam"],
            type="filepath",
            label="",
            show_label=False,
            elem_id="chat-attach",
            visible=False,
            height=110,
        )

        with gr.Row(elem_id="input-bar"):
            attach_btn = gr.Button("📎", elem_id="attach-btn", scale=0, min_width=44)
            msg_inp = gr.Textbox(
                placeholder="Escribe un mensaje…",
                show_label=False,
                elem_id="msg-inp",
                scale=4,
                lines=1,
                max_lines=3,
            )
            send_btn = gr.Button("➤", elem_id="send-btn", scale=0, min_width=44)

    # ── Eventos ────────────────────────────────────────────────────────────────
    verify_btn.click(
        fn=verify_fn,
        inputs=[name_inp, selfie],
        outputs=[verify_msg, token_state, auth_col, chat_col, chat_disp, chat_hist],
    )

    attach_btn.click(
        fn=toggle_attach,
        inputs=[img_vis],
        outputs=[attach_img, img_vis],
    )

    send_btn.click(
        fn=send_fn,
        inputs=[token_state, msg_inp, attach_img, chat_hist, img_vis],
        outputs=[chat_disp, chat_hist, msg_inp, attach_img, img_vis],
    )
    msg_inp.submit(
        fn=send_fn,
        inputs=[token_state, msg_inp, attach_img, chat_hist, img_vis],
        outputs=[chat_disp, chat_hist, msg_inp, attach_img, img_vis],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("UI_PORT", 7860)),
        css=_CSS,
        head=_HEAD,
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.blue,
            neutral_hue=gr.themes.colors.slate,
            font=[gr.themes.GoogleFont("DM Sans"), "sans-serif"],
        ),
    )
