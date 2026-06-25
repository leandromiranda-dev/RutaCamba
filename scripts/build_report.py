# -*- coding: utf-8 -*-
"""Genera report.pdf (10 paginas, formato pregunta-respuesta) para RutaCamba."""
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Image, KeepTogether, ListFlowable, ListItem, HRFlowable
)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "report.pdf")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("TitlePage", fontSize=22, leading=26, alignment=TA_CENTER,
                           textColor=colors.HexColor("#16324f"), spaceAfter=10, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("SubtitlePage", fontSize=13, leading=18, alignment=TA_CENTER,
                           textColor=colors.HexColor("#2c6e9e"), spaceAfter=6))
styles.add(ParagraphStyle("MetaPage", fontSize=10.5, leading=15, alignment=TA_CENTER,
                           textColor=colors.HexColor("#444444")))
styles.add(ParagraphStyle("H1", fontSize=15, leading=18, spaceBefore=4, spaceAfter=8,
                           textColor=colors.HexColor("#16324f"), fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("H2", fontSize=11.5, leading=14, spaceBefore=10, spaceAfter=4,
                           textColor=colors.HexColor("#2c6e9e"), fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("Q", fontSize=10.3, leading=13.5, spaceBefore=8, spaceAfter=2,
                           textColor=colors.HexColor("#a3401a"), fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("A", fontSize=10, leading=13.3, spaceAfter=4, alignment=TA_JUSTIFY))
styles.add(ParagraphStyle("Small", fontSize=8.3, leading=10.8, textColor=colors.HexColor("#555555")))
styles.add(ParagraphStyle("Caption", fontSize=8.3, leading=10.5, alignment=TA_CENTER,
                           textColor=colors.HexColor("#555555"), spaceAfter=8))
styles.add(ParagraphStyle("Foot", fontSize=8, leading=10, textColor=colors.HexColor("#888888")))

GREEN = colors.HexColor("#1e7d4f")
RED = colors.HexColor("#b3261e")
LIGHT = colors.HexColor("#eef3f8")

story = []

def Q(text):
    story.append(Paragraph("P: " + text, styles["Q"]))

def A(text):
    story.append(Paragraph("R: " + text, styles["A"]))

def H1(text):
    story.append(Paragraph(text, styles["H1"]))

def H2(text):
    story.append(Paragraph(text, styles["H2"]))

def hr():
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#cccccc"), spaceBefore=4, spaceAfter=6))

def img(path=None, width=14*cm, caption=None, max_height=9*cm, _into=None, path_=None):
    target = _into if _into is not None else story
    path = path_ if path_ is not None else path
    full = os.path.join(BASE, path)
    if os.path.exists(full):
        try:
            from PIL import Image as PILImage
            iw, ih = PILImage.open(full).size
            h = width * ih / iw
            if h > max_height:
                h = max_height
                width = h * iw / ih
            im = Image(full, width=width, height=h)
            im.hAlign = "CENTER"
            target.append(im)
            if caption:
                target.append(Paragraph(caption, styles["Caption"]))
        except Exception as e:
            target.append(Paragraph(f"[No se pudo insertar {path}: {e}]", styles["Small"]))
    else:
        target.append(Paragraph(f"[Imagen no encontrada: {path}]", styles["Small"]))

def metric_table(rows, header, col_widths=None):
    data = [header] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16324f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.3),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbbbbb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t

# ============================================================ PORTADA
story.append(Spacer(1, 4.5*cm))
story.append(Paragraph("Asistente Turístico Inteligente", styles["TitlePage"]))
story.append(Paragraph("RutaCamba — Reconocimiento de Lugares, Verificación de Identidad<br/>y Traducción Multilingüe", styles["SubtitlePage"]))
story.append(Spacer(1, 0.8*cm))
story.append(HRFlowable(width="60%", thickness=1, color=colors.HexColor("#2c6e9e"), hAlign="CENTER"))
story.append(Spacer(1, 0.8*cm))
story.append(Paragraph("Informe de Proyecto Final<br/>Redes Neuronales y Aprendizaje Profundo", styles["MetaPage"]))
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph("Universidad Católica Boliviana &ldquo;San Pablo&rdquo; — Sede Santa Cruz", styles["MetaPage"]))
story.append(Spacer(1, 1.2*cm))
story.append(Paragraph(
    "Equipo: Diego Lewenstein (Datos) · Leandro Miranda (Re-ID, embeddings) · "
    "Jose Alfredo (Re-ID, LLM, entrenamiento B2/B3/BA) · Alejandro Ojeda (Landmarks, B1/B2) · "
    "Nicole Lozada (WandB, API/UI, informe)", styles["MetaPage"]))
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph("Repositorio: github.com/leandromiranda-dev/RutaCamba &nbsp;·&nbsp; "
                        "WandB: wandb.ai/lozadaleonn-ciencialink/rutacamba", styles["MetaPage"]))
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph("Santa Cruz de la Sierra, junio de 2026", styles["MetaPage"]))
story.append(PageBreak())

# ============================================================ PÁGINA 2 — Contexto y objetivos
H1("1. Contexto y objetivos del proyecto")
Q("¿Qué problema resuelve el sistema y para quién?")
A("RutaCamba es el sistema técnico que responde al enunciado de negocio de "
  "&ldquo;RutaCruceña&rdquo;: una app de turismo para guías acreditados de Santa Cruz de la Sierra. "
  "El guía apunta la cámara a un lugar emblemático y el sistema responde con el nombre del sitio, "
  "una descripción y traducciones, sin depender de GPS. Por ser un servicio de pago, cada solicitud "
  "de reconocimiento se condiciona a una verificación previa de identidad (re-identificación biométrica), "
  "evitando llamadas no autorizadas al modelo de visión.")
Q("¿Cuál es el flujo end-to-end exigido y cómo se mapea a los módulos del sistema?")
A("(1) El usuario declara una identidad y sube una selfie → <b>Módulo A (Re-ID)</b> decide si concede acceso "
  "comparando el embedding contra la galería de guías registrados bajo un umbral de distancia. "
  "(2) Con acceso concedido, sube la foto de un lugar → <b>Módulo B</b> predice el landmark (top-k + probabilidades) "
  "con dos enfoques entrenados sobre el mismo dataset: B1 (CNN desde cero) y B2 (arquitectura con bloques residuales, "
  "nombrada BA en el código, comparada frente a B1). (3) La respuesta se traduce a inglés, francés e italiano → "
  "<b>Módulo C (LLM)</b>, con fallback offline si el LLM falla. (4) Todo el entrenamiento quedó registrado en "
  "<b>Módulo D (WandB)</b>. (5) Todo se sirve mediante <b>Módulo E</b>: una API FastAPI y una interfaz web (React) "
  "que la consume.")
Q("¿Qué arquitectura general de software se usó?")
A("Backend: FastAPI + PyTorch (TorchScript para inferencia) + facenet-pytorch (FaceNet/InceptionResnetV1, Re-ID) + LLM vía OpenRouter/Gemini "
  "con fallback NLLB-200. Frontend: React + TypeScript + Vite + Tailwind, con soporte PWA. Tracking: Weights &amp; Biases "
  "(proyecto <font face='Courier'>lozadaleonn-ciencialink/rutacamba</font>). El repositorio organiza el código en "
  "<font face='Courier'>src/data, src/landmarks, src/reid, src/translation, api/, web/, ETL/, notebooks/, docs/decisiones/</font>, "
  "siguiendo la estructura sugerida por el enunciado.")
H2("Nota de alcance sobre la interfaz")
A("El enunciado permite Gradio o Streamlit como interfaz mínima; el equipo optó por construir además una interfaz "
  "web propia en React consumiendo la misma API, documentada en <font face='Courier'>web/README.md</font> y servida en "
  "el puerto 5173 durante desarrollo.")
story.append(PageBreak())

# ============================================================ PÁGINA 3 — Módulo A: Re-ID
H1("2. Módulo A — Verificación de identidad por Re-ID")
Q("¿Qué modelo de embeddings se usó y por qué, en lugar de ArcFace o VGG-Face?")
A("Se usó <b>FaceNet</b> —en concreto <font face='Courier'>InceptionResnetV1</font> preentrenado en <b>VGGFace2</b>, "
  "vía la librería <font face='Courier'>facenet-pytorch</font> (detección del rostro con MTCNN + extracción del embedding "
  "de 512-d). FaceNet entrena con <i>Triplet Loss</i>, que optimiza directamente el espacio de embeddings para que las "
  "imágenes de una misma identidad queden cercanas y las de identidades distintas queden separadas por un margen, "
  "produciendo vectores compactos y L2-normalizados robustos a cambios de iluminación y pose. Se eligió FaceNet por "
  "integrarse de forma nativa con el stack PyTorch del resto del proyecto —sin sumar la dependencia pesada de "
  "DeepFace/TensorFlow— y por ofrecer un pipeline MTCNN+InceptionResnetV1 listo y bien mantenido. Se descartó VGG-Face "
  "por ser una arquitectura más antigua con embeddings menos discriminativos para clusters complejos.")
Q("¿Cómo se agregan varias fotos de referencia por identidad en la galería?")
A("Por <b>distancia mínima</b> (best-match): la identidad queda representada por su foto más cercana al probe. "
  "Se descartó el promedio porque es más sensible a fotos borrosas o con mal encuadre, y el centroide porque con "
  "solo 3–5 fotos por identidad es inestable.")
Q("¿Qué métrica de distancia se usó y por qué coseno y no euclidiana?")
A("Distancia coseno (1 − cos(a,b)). Los embeddings de FaceNet están L2-normalizados sobre la hiperesfera unitaria, "
  "de modo que la <i>dirección</i> del vector concentra toda la información discriminativa y su magnitud no aporta "
  "señal; la distancia coseno es la métrica natural en ese espacio, mientras que la euclidiana introduciría ruido de "
  "escala. Con FaceNet+coseno, los pares genuinos (misma persona) quedan a una distancia notablemente menor que los "
  "impostores, dando una separación clara para fijar el umbral.")
Q("¿Cómo se justificó el umbral de acceso?")
A("El umbral de partida es 0.65 (<font face='Courier'>config.REID_THRESHOLD</font>), tomado como punto de partida "
  "razonable para FaceNet+coseno y pensado para ajustarse formalmente. El método formal para calibrarlo es ROC/EER: se generan "
  "distribuciones de distancias intra-clase (misma persona) e inter-clase (personas distintas) sobre la galería real "
  "del equipo, se traza la curva ROC y se elige el punto donde la tasa de falsos aceptos (FPR) iguala a la de falsos "
  "rechazos (FNR). Esta calibración final con la galería poblada (<font face='Courier'>data/gallery/embeddings_autorizados.pt</font>) "
  "se ejecuta en <font face='Courier'>notebooks/02b_reid_ranking_metrics.ipynb</font>.")
Q("¿Cómo se midió la calidad de la recuperación (top-1, top-k, mAP)?")
A("El mAP de re-ID se implementó de forma manual sobre listas rankeadas por <i>query</i>: para cada consulta se calcula "
  "el Average Precision (AP) acumulando la precisión en cada posición relevante del ranking, y el mAP es el promedio de "
  "los AP sobre todas las consultas. Esto difiere del mAP de detección de objetos, que promedia sobre clases usando IoU "
  "y el área bajo la curva precisión-recall: el de re-ID viene de recuperación de información (ranking por similitud), "
  "no de localización con cajas. Se descartó <font face='Courier'>sklearn.average_precision_score</font> de forma directa "
  "porque está pensado para clasificación binaria/multietiqueta, no para listas de recuperación indexadas por distancia.")
Q("¿Cómo se visualizó el espacio de embeddings?")
A("Con <b>t-SNE</b>, no PCA. PCA es una proyección lineal que preserva varianza global y, con embeddings de alta "
  "dimensionalidad, tiende a superponer las identidades en una nube indistinguible en 2D. t-SNE preserva la estructura "
  "de vecindad local y permite ver clusters separados por identidad, evidencia directa de que el entrenamiento por "
  "<i>triplet loss</i> de FaceNet extrajo características discriminativas.")
H2("Cómo se registró en WandB sin un loop de entrenamiento")
A("FaceNet (InceptionResnetV1/VGGFace2) es preentrenado y no se afina en este proyecto, por lo que no hay épocas. Para no dejar vacío el "
  "dashboard de Fase 2, se registra un run de <i>evaluación</i> (<font face='Courier'>reid_eval</font>) con un único "
  "step: se loguean los hiperparámetros fijos (modelo, métrica de distancia, umbral) y las métricas finales "
  "(top-1, top-k, mAP) una vez calibradas sobre la galería real, documentando el experimento sin simular un "
  "entrenamiento que no existió.")
story.append(PageBreak())

# ============================================================ PÁGINA 4 — Dataset
H1("3. Dataset de lugares locales (Módulo B, Fase 1)")
Q("¿Qué dataset se construyó y cuántas clases/imágenes tiene?")
A("Un dataset propio de <b>8 clases</b> de lugares emblemáticos de Santa Cruz de la Sierra — por encima del mínimo "
  "exigido —: <i>Cambodromo, CatedralMunicipal, Cristo, DunasArena, ParqueUrbano, Plaza24, Tahuichi y Ventura</i>. "
  "Total: <b>790 imágenes</b>, particionadas 70/15/15 (train=553, val=118, test=119), con un split estratificado "
  "(<font face='Courier'>train_test_split(stratify=y)</font>) que preserva la proporción de cada clase en los tres "
  "subconjuntos sin solapamiento de imágenes.")
Q("¿Por qué 70/15/15 y no la proporción clásica 80/10/10?")
A("Con 790 imágenes, 80/10/10 dejaría solo ~79 imágenes de test (~9–10 por clase), con alta varianza estadística en "
  "las métricas. El 70/15/15 da 118–119 imágenes en val/test (~14–15 por clase), suficientes para estimaciones más "
  "estables del accuracy por clase, incluso en la clase minoritaria (CatedralMunicipal, 61 imágenes).")
Q("¿Cómo se manejó el desbalance de clases?")
A("El ratio mayoritaria/minoritaria es 2.82x (Ventura=172 vs. CatedralMunicipal=61). Se aplicó "
  "<font face='Courier'>WeightedRandomSampler</font> con pesos inversos a la frecuencia de cada clase "
  "(guardados en <font face='Courier'>data/class_weights.json</font>), en lugar de oversampling físico, que "
  "duplicaría imágenes exactas y aumentaría el riesgo de overfitting en las clases pequeñas.")
Q("¿Qué preprocesamiento y augmentation se aplicó?")
A("Preprocesamiento: corrección de orientación EXIF (<font face='Courier'>exif_transpose</font>, necesaria porque PIL "
  "ignora por defecto esa metadata), <font face='Courier'>Resize(256) → CenterCrop(224)</font> y normalización con "
  "media/desviación de ImageNet (requerida para Transfer Learning). Augmentation en train, moderado por diseño: "
  "RandomCrop(224), flip horizontal (p=0.5), rotación ±10° y jitter de color — sin flips verticales ni rotaciones "
  "grandes, porque deformarían la geometría característica de los monumentos, que es la señal discriminativa principal. "
  "Antes del split se purgaron near-duplicates por perceptual hash (pHash) para evitar fuga de información entre train y test.")
img("docs/decisiones/eda_distribucion.png", caption="Figura 1 — Distribución de clases del dataset (docs/decisiones/eda_distribucion.png).")
story.append(PageBreak())

# ============================================================ PÁGINA 5 — B1 CNN
H1("4. Módulo B — Enfoque B1: CNN desde cero")
Q("¿Qué arquitectura propia se diseñó y por qué 4 bloques en vez de 3?")
A("<b>TuristCNN</b>: 4 bloques Conv3×3 → BatchNorm → ReLU → MaxPool2×2 (32→64→128→256 canales), seguidos de "
  "AdaptiveAvgPool2d(1), Dropout(0.5), FC(256→128) con ReLU, Dropout(0.3) y FC(128→8). Total: <b>422,824 parámetros</b> "
  "(1.75 MB exportado). Se eligieron 4 bloques —por encima del mínimo de 3 que pide la rúbrica— porque con solo 3 el "
  "campo receptivo final resulta insuficiente para distinguir detalles arquitectónicos finos entre landmarks distintos; "
  "5 o más bloques se descartaron por el alto riesgo de overfitting con un dataset de 553 imágenes de entrenamiento.")
Q("¿Por qué AdaptiveAvgPool2d en vez de Flatten directo antes de la cabeza FC?")
A("Aplanar el mapa de activación final (256×14×14) daría una FC de entrada ~50.000 dimensiones (decenas de millones de "
  "pesos), excesivo para 8 clases y un dataset pequeño. AdaptiveAvgPool2d(1) reduce eso a un vector de 256, llevando "
  "la primera capa FC a ~33K pesos: menos parámetros que aprender, menor riesgo de overfitting.")
Q("¿Cómo se entrenó y qué resultado dio?")
A("Función de pérdida: CrossEntropyLoss; optimizador: Adam (lr=1e-3, weight_decay=1e-4); 30 épocas, batch_size=32, "
  "con el WeightedRandomSampler de Fase 1 activo. Se guardó el checkpoint de menor val_loss (no el de la última época), "
  "para evitar quedarse con un modelo ya sobreajustado en las épocas finales. <b>Resultado: val_acc = 91.53% "
  "(época 29, val_loss = 0.3368), test_acc = 90.76%</b> — la brecha val/test de solo 0.77 pp indica que no hubo "
  "overfitting relevante, y supera ampliamente el umbral mínimo de la rúbrica (≥45%).")
Q("¿Cómo se exportó y verificó el modelo?")
A("Con TorchScript (<font face='Courier'>torch.jit.script</font>), guardado en <font face='Courier'>models/cnn_scratch.pt</font>. "
  "La exportación se hace siempre desde una copia del modelo en CPU para que el <font face='Courier'>.pt</font> sea "
  "portable a una máquina sin GPU (la API de despliegue no requiere CUDA), y se valida con una pasada de inferencia "
  "de prueba tras recargarlo.")
H2("Métricas de test detalladas (B1)")
rows = [
    ["Test Accuracy", "Precision (macro)", "Recall (macro)", "F1 (macro)", "Parámetros", "Tamaño"],
    ["90.76%", "92.12%", "88.89%", "89.87%", "422,824", "1.75 MB"],
]
tail = [metric_table(rows[1:], rows[0]), Spacer(1, 0.25*cm)]
img(_into=tail, path_="docs/eval/confusion_b1.png", width=7.5*cm, caption="Figura 2 — Matriz de confusión de B1 sobre el test set (docs/eval/confusion_b1.png).", max_height=6.2*cm)
story.append(KeepTogether(tail))
story.append(PageBreak())

# ============================================================ PÁGINA 6 — B2/BA + comparación
H1("5. Módulo B — Enfoque B2: arquitectura con bloques residuales (BA)")
A("<i>Nota de transparencia:</i> en el código del repositorio, el segundo enfoque entrenado para esta demo se llama "
  "<b>BA (TuristResNet)</b>: una red con bloques residuales <b>entrenada desde cero</b> (sin pesos preentrenados de "
  "ImageNet). El repositorio incluye además un B2 real con Transfer Learning sobre ResNet18 preentrenado "
  "(99.15% val / 100% test, ver <font face='Courier'>ReporteJoseAlfredo.md</font>), pero la comparación oficial que "
  "se documenta y demuestra en esta entrega es <b>B1 vs. BA</b>, por decisión explícita del equipo para la demo.")
Q("¿Qué arquitectura tiene BA y qué buscaba demostrar?")
A("Stem Conv7×7 (stride=2) + MaxPool → 3 bloques residuales (64→64, 64→128 stride=2, 128→256 stride=2, cada uno con "
  "shortcut 1×1 cuando cambia la dimensión) → GlobalAvgPool → FC(256→128→8). Total: <b>1,266,632 parámetros</b> "
  "(5.15 MB). El objetivo era medir si las skip connections —que en teoría permiten gradientes más directos y redes "
  "más profundas sin degradación— se traducen en una mejora real frente a B1 cuando el dataset es pequeño (553 imágenes).")
Q("¿BA superó a B1? ¿Qué explica el resultado?")
A("<b>No.</b> BA obtuvo val_acc = 92.37% pero <b>test_acc = 87.39%</b>, por debajo del 90.76% de B1. La brecha "
  "val/test de BA (4.98 pp) es mucho mayor que la de B1 (0.77 pp), señal de overfitting moderado: 1.27M de parámetros "
  "son demasiados para 553 imágenes de entrenamiento. Además, el stem 7×7 con stride=2 reduce la resolución muy pronto, "
  "lo que perjudica clases con detalles finos (Tahuichi cae a 73% de recall). Conclusión de la defensa: las skip "
  "connections ayudan cuando hay suficientes datos para aprovechar la profundidad adicional; con un dataset chico, "
  "una CNN más simple y bien regularizada (B1) generaliza mejor.")
Q("¿Cómo se diseñó la comparación para que fuera justa?")
A("Mismos hiperparámetros (30 épocas, Adam, batch_size=32), mismo split train/val/test, mismo pipeline de "
  "preprocesamiento y augmentation, y evaluación final en un único paso reproducible "
  "(<font face='Courier'>scripts/evaluate_test.py</font>) que corre ambos modelos sobre el test set sin volver a "
  "tocarlo, reportando accuracy, precision/recall/F1 macro y matriz de confusión por clase.")
H2("Tabla comparativa B1 vs. BA")
rows = [
    ["Modelo", "Test Acc.", "Precision", "Recall", "F1 (macro)", "Parámetros", "Tamaño", "Tiempo entren."],
    ["B1 — CNN desde cero", "90.76%", "92.12%", "88.89%", "89.87%", "422,824", "1.75 MB", "~53 min"],
    ["BA — ResNet-lite (residual)", "87.39%", "86.49%", "84.55%", "85.35%", "1,266,632", "5.15 MB", "~49 min"],
]
tail2 = [metric_table(rows[1:], rows[0], col_widths=[3.6*cm, 1.6*cm, 1.7*cm, 1.6*cm, 1.7*cm, 2.0*cm, 1.6*cm, 1.9*cm]), Spacer(1, 0.25*cm)]
img(_into=tail2, path_="docs/eval/confusion_ba.png", width=7.5*cm, caption="Figura 3 — Matriz de confusión de BA sobre el test set (docs/eval/confusion_ba.png).", max_height=6.2*cm)
story.append(KeepTogether(tail2))
story.append(PageBreak())

# ============================================================ PÁGINA 7 — LLM
H1("6. Módulo C — Traducción multilingüe con LLM")
Q("¿Qué LLM se usó y cómo se evita llamar al modelo en cada solicitud?")
A("Se usa <b>google/gemini-2.5-flash-lite</b> vía OpenRouter. La estrategia es de tres niveles: (1) un diccionario "
  "estático embebido en el código con 8 landmarks × 4 idiomas como base de emergencia; (2) traducciones "
  "<b>pre-generadas offline</b> y guardadas en <font face='Courier'>data/translations.json</font> "
  "(<font face='Courier'>scripts/generate_translations.py</font>), consultadas en O(1) en cada request; (3) llamada "
  "en vivo al LLM solo si se pide un idioma fuera del set offline. Se descartó llamar al LLM en cada request por "
  "latencia (~2s vs. lookup instantáneo), costo variable acumulativo y dependencia de conexión en la demo.")
Q("¿Cómo se normalizan consultas en un idioma inesperado?")
A("Con el mismo LLM, no con un traductor literal. Ejemplo de la bitácora: la consulta "
  "&ldquo;Where is the big Jesus statue?&rdquo; debe mapearse a &ldquo;Cristo Redentor&rdquo; (el nombre real del "
  "landmark), algo que un traductor literal no resuelve (devolvería la traducción literal de la pregunta, no el "
  "nombre de la clase). El LLM entiende intención semántica y tolera errores ortográficos o referencias culturales.")
Q("¿Qué pasa si el LLM falla (timeout, sin conexión, respuesta vacía)?")
A("Cae a <b>NLLB-200 distilled (600M, Meta/HuggingFace)</b> como fallback completamente offline, con carga perezosa "
  "(<i>lazy</i>): el modelo de ~2.4 GB solo se instancia si el LLM efectivamente falla, evitando el costo de cargarlo "
  "en el caso feliz. Se descartó MarianMT (un modelo separado por cada par de idiomas, &gt;1 GB acumulado) y Google "
  "Translate (requiere internet, no es un fallback offline real). El sistema nunca devuelve un error duro al usuario "
  "por un fallo del LLM: siempre hay una traducción disponible, aunque sea de menor calidad.")
H2("Idiomas y alcance")
A("Cobertura mínima exigida: inglés, francés e italiano, sobre las 8 clases del dataset. El selector de idioma de la "
  "interfaz ofrece adicionalmente español y, cuando el LLM está disponible, otros idiomas vía NLLB-200.")
story.append(PageBreak())

# ============================================================ PÁGINA 8 — WandB
H1("7. Módulo D — Experiment tracking con WandB")
Q("¿Por qué WandB y no MLflow o TensorBoard?")
A("Decisión documentada por el equipo: (1) dashboards compartibles por enlace, sin levantar un servidor propio "
  "(clave para revisar resultados en equipo); (2) vista nativa de <i>parallel coordinates</i> para comparar runs de "
  "CNN-desde-cero vs. arquitecturas alternativas, exigida implícitamente por el enunciado; (3) gestión de artifacts "
  "integrada (<font face='Courier'>wandb.Artifact(type='model')</font>) para versionar los <font face='Courier'>.pt</font> "
  "exportados; (4) soporte de hyperparameter sweeps sin infraestructura adicional. MLflow exige un servidor de "
  "tracking propio y TensorBoard no ofrece dashboards públicos ni artifacts versionados de forma nativa.")
Q("¿Qué se registró en cada run?")
A("Para B1 y BA: curvas de train/val loss y accuracy por época, la configuración completa (arquitectura, "
  "learning rate, batch size, optimizador) y el mejor checkpoint como artifact. Para Re-ID (que no tiene épocas de "
  "entrenamiento, ya que FaceNet es preentrenado): un run de evaluación con un único step, logueando los "
  "hiperparámetros fijos y las métricas finales (top-1, top-k, mAP), de forma que el dashboard documente el "
  "experimento sin simular un entrenamiento inexistente.")
H2("Enlaces a WandB (proyecto: lozadaleonn-ciencialink/rutacamba)")
rows = [
    ["Modelo / experimento", "Run ID", "Métrica clave", "Enlace"],
    ["B1 — CNN desde cero", "g3630v5v", "val_acc 91.53% / test 90.76%",
     "wandb.ai/lozadaleonn-ciencialink/rutacamba/runs/g3630v5v"],
    ["BA — ResNet-lite (residual)", "3i5ickz4", "val_acc 92.37% / test 87.39%",
     "wandb.ai/lozadaleonn-ciencialink/rutacamba/runs/3i5ickz4"],
    ["B2 (TL, ResNet18) — referencia", "enedjxj9", "val_acc 99.15% / test 100%",
     "wandb.ai/lozadaleonn-ciencialink/rutacamba/runs/enedjxj9"],
    ["B3 — SE-CNN — referencia", "wbay2jxu", "val_acc 92.37% / test 92.44%",
     "wandb.ai/lozadaleonn-ciencialink/rutacamba/runs/wbay2jxu"],
]
story.append(metric_table(rows[1:], rows[0], col_widths=[4.6*cm, 1.7*cm, 3.6*cm, 6.0*cm]))
story.append(Spacer(1, 0.25*cm))
story.append(Paragraph(
    "<i>B2 y B3 se entrenaron como exploración adicional del equipo (Transfer Learning real con ResNet18 preentrenado, "
    "y una CNN-desde-cero con atención Squeeze-and-Excitation) y se referencian aquí por trazabilidad y para la "
    "vista de comparación de runs en WandB, aunque la comparación oficial reportada en este informe sea B1 vs. BA.</i>",
    styles["Small"]))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "[ESPACIO PARA CAPTURA] — Insertar aquí una captura del dashboard de WandB con la vista de comparación de runs "
    "(parallel coordinates o gráfico superpuesto de val_acc / val_loss de B1 vs. BA). Sugerencia de archivo: "
    "<font face='Courier'>docs/eval/wandb_comparacion.png</font>.", styles["Small"]))
story.append(PageBreak())

# ============================================================ PÁGINA 9 — API/UI
H1("8. Módulo E — API (FastAPI) e interfaz")
Q("¿Qué endpoints mínimos expone la API y cómo se condiciona el acceso?")
A("<font face='Courier'>POST /verify</font> (selfie + identidad declarada → token de sesión si el Re-ID aprueba), "
  "<font face='Courier'>POST /predict</font> (requiere token válido; foto del lugar → landmark + top-k + "
  "probabilidades + traducciones), <font face='Courier'>POST /place/info</font> (descripción en el idioma elegido) "
  "y <font face='Courier'>POST /chat</font> (conversación sobre el lugar, si hay LLM disponible). "
  "<font face='Courier'>/predict</font> rechaza la solicitud si no se presenta un token emitido por "
  "<font face='Courier'>/verify</font>, cumpliendo el requisito de que ninguna predicción se sirva sin identidad "
  "verificada.")
Q("¿Por qué cargar los modelos al iniciar la API y no en cada request?")
A("Los modelos TorchScript (<font face='Courier'>cnn_scratch.pt</font>, el de BA, y el servicio de traducción) se "
  "instancian una sola vez en el <i>lifespan</i> de FastAPI al arrancar el proceso. Cargar pesos desde disco en cada "
  "request añadiría latencia de I/O innecesaria a cada predicción; la API nunca re-entrena, solo consume los "
  ".pt ya exportados, tal como exige el enunciado.")
Q("¿Cómo se maneja la sesión entre /verify y /predict?")
A("Token en memoria con expiración (TOKEN_TTL = 3600 s), asociado a la identidad y el rol del usuario. Se eligió "
  "frente a JWT o base de datos por simplicidad: para una demo de un solo proceso no se justifica la complejidad de "
  "persistencia distribuida o firma criptográfica de tokens.")
Q("¿Qué interfaz consume la API y qué muestra?")
A("Una interfaz web en React (alternativa equivalente a Gradio/Streamlit, también consumiendo la misma API REST) con "
  "pantallas de login (captura de selfie + nombre), tour (subida de foto del lugar, predicción top-k con "
  "probabilidades y traducciones) y administración (alta de nuevas identidades en la galería). El flujo completo "
  "—verificación, predicción, traducción— se demuestra en vivo contra la API real, sin mocks, salvo el modo "
  "<font face='Courier'>REID_MOCK=1</font> usado solo para desarrollo de UI sin cámara disponible.")
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph(
    "[ESPACIO PARA CAPTURA] — Insertar aquí 1–2 capturas de la interfaz en ejecución mostrando el flujo end-to-end "
    "(login → predicción top-k → traducción). Sugerencia: capturar la app corriendo en localhost:5173 y guardar en "
    "<font face='Courier'>docs/eval/ui_demo.png</font>.", styles["Small"]))
story.append(Spacer(1, 0.25*cm))
img("desing/inicio_y_autenticaci_n_facial/screen.png", width=8.5*cm,
    caption="Figura 4 — Mockup de diseño de la pantalla de login/autenticación facial (desing/inicio_y_autenticaci_n_facial/screen.png).")
story.append(PageBreak())

# ============================================================ PÁGINA 10 — Conclusiones
H1("9. Resultados finales, limitaciones y conclusiones")
H2("Resumen de métricas finales")
rows = [
    ["Módulo", "Resultado clave"],
    ["A — Re-ID", "FaceNet (InceptionResnetV1/VGGFace2) + coseno, umbral 0.65 (a calibrar por ROC/EER con galería real); ranking por distancia mínima"],
    ["B — B1 (CNN scratch)", "Test Acc. 90.76% · F1 macro 89.87% · 422,824 parámetros · cumple umbral ≥45%"],
    ["B — BA (ResNet-lite)", "Test Acc. 87.39% · F1 macro 85.35% · 1,266,632 parámetros · no supera a B1"],
    ["C — LLM", "EN/FR/IT vía Gemini-2.5-flash-lite + fallback NLLB-200; normalización semántica de consultas"],
    ["D — WandB", "4 runs registrados (B1, BA, B2, B3) en lozadaleonn-ciencialink/rutacamba con artifacts"],
    ["E — API/UI", "FastAPI con /verify→/predict condicionado, interfaz web consumiendo la API end-to-end"],
]
story.append(metric_table(rows[1:], rows[0], col_widths=[3.6*cm, 12.8*cm]))
story.append(Spacer(1, 0.3*cm))
Q("¿Cuál es la conclusión central de la comparación B1 vs. BA?")
A("Para este dataset (790 imágenes, 8 clases visualmente bien diferenciadas), una CNN simple, poco profunda y "
  "regularizada con dropout (B1, 423K parámetros) generaliza mejor en test que una variante con bloques residuales "
  "y 3× más parámetros (BA). Las skip connections no son una mejora automática: ayudan a entrenar redes más "
  "profundas sin degradación del gradiente, pero esa ventaja solo se traduce en mejor accuracy de test cuando hay "
  "suficiente cantidad de datos para que la capacidad adicional generalice en lugar de sobreajustar.")
Q("¿Qué es overfitting y cómo se detectó en este proyecto?")
A("Overfitting es cuando el modelo memoriza patrones específicos del set de entrenamiento que no generalizan a datos "
  "nuevos, evidenciado por una brecha creciente entre métricas de entrenamiento/validación y las de test. Se detectó "
  "comparando val_acc vs. test_acc: B1 (91.53% vs. 90.76%, brecha 0.77 pp) prácticamente no sobreajusta; BA (92.37% "
  "vs. 87.39%, brecha 4.98 pp) sí muestra overfitting moderado. Se mitigó con dropout en la cabeza FC, "
  "augmentation moderado en train, weight_decay en el optimizador y deteniendo el entrenamiento en el checkpoint de "
  "menor val_loss en lugar de la última época.")
Q("¿Qué quedó pendiente o como limitación conocida?")
A("La calibración final del umbral de Re-ID por ROC/EER sobre la galería real del equipo debe consolidarse en "
  "<font face='Courier'>notebooks/02b_reid_ranking_metrics.ipynb</font> con salidas ejecutadas y visibles. El test set "
  "de clasificación (119 imágenes) es pequeño: las métricas de la clase minoritaria (CatedralMunicipal, ~9 imágenes "
  "en test) tienen mayor varianza que las de clases con más muestras. El video de demo y la defensa oral son los "
  "entregables finales de la Fase 7, coherentes con lo documentado en este informe.")
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph(
    "Repositorio: github.com/leandromiranda-dev/RutaCamba &nbsp;·&nbsp; "
    "WandB: wandb.ai/lozadaleonn-ciencialink/rutacamba &nbsp;·&nbsp; "
    "Bitácoras de decisiones completas: docs/decisiones/", styles["Foot"]))

doc = SimpleDocTemplate(
    OUT, pagesize=LETTER,
    leftMargin=2.1*cm, rightMargin=2.1*cm, topMargin=1.8*cm, bottomMargin=1.8*cm,
    title="Informe RutaCamba - Asistente Turistico Inteligente",
)
doc.build(story)
print("OK ->", OUT)
