# Fase 7 — Informe, video y defensa · Nicole Lozada (coordina; todos aportan)

**Peso:** 40 pts — **la fase más pesada del proyecto.** · **Archivos:** `README.md`,
`report.pdf`, y la **guía de estudio** ensamblada desde `docs/decisiones/`.

> Aunque todo el código funcione perfecto (60 pts de Fases 1–6), acá se juegan 40
> puntos: informe + video + defensa. Y la defensa es **individual** — la rúbrica dice
> que puede bajar la nota de quien no demuestre comprensión de su parte. Por eso la
> regla de documentar decisiones aplicó a todos desde el día 1: esas bitácoras son
> la materia prima de esta fase.

---

## 1. Archivos que te pertenecen

| Archivo | Qué va adentro |
|---------|----------------|
| `README.md` | instalación, arranque de cada módulo, API/UI, descripción del proyecto |
| `report.pdf` | informe de 10 páginas, formato pregunta–respuesta |
| `docs/guia_de_estudio.md` | (nueva) ensamblada juntando todas las `docs/decisiones/` |

---

## 2. Paso a paso

1. **Recolectá las bitácoras:** juntá los 6–7 archivos de `docs/decisiones/` (Diego,
   Leandro, Jose×2, Alejandro, Nicole×2). Cada decisión documentada ("por qué esto y no
   lo otro") se convierte en una pregunta-respuesta de la **guía de estudio**
   (`docs/guia_de_estudio.md`). Esto es lo que cada uno estudia para su defensa.

2. **Informe `report.pdf` (10 páginas, pregunta–respuesta):** redactá en Word/Google
   Docs y exportá a PDF. Estructura sugerida por módulo, respondiendo los ejes de
   defensa del enunciado:
   - Arquitecturas elegidas y nº de parámetros (CNN vs ResNet18)
   - Diferencia clasificación vs re-ID
   - Qué representa el espacio de embeddings y cómo eligieron el umbral
   - Overfitting (cómo lo detectaron/mitigaron)
   - Cómo midieron el mAP de re-ID y por qué difiere del de detección
   - Manejo de fallo del LLM (fallback)
   - Comparación de runs en WandB (B1 vs B2)
   Insertá **capturas de los dashboards de WandB + enlaces compartibles**.

3. **Video (3–5 min)** con OBS Studio: mostrá el flujo end-to-end en vivo en la
   interfaz — verificación → predicción top-k → traducciones. Que sea **coherente con
   el informe**.

4. **README.md:** comandos de arranque (`uvicorn api.main:app --reload`,
   `python ui/app.py`), variables de entorno (clave LLM, puertos 8000/7860), cómo
   reconstruir el dataset desde S3, cómo bajar los modelos, y enlace al proyecto de
   WandB. Ensamblá el `requirements.txt` final juntando los `requirements/faseN.txt`
   (sin duplicados: `pip-compile` o manual).

5. **Ensayo de defensa:** repartí los ejes de pregunta del enunciado entre los
   integrantes según su fase. Cada uno responde desde SU bitácora. Hagan un simulacro.

---

## 3. Checklist de rúbrica

- [ ] Informe claro y bien estructurado (pregunta–respuesta) con decisiones y resultados (5)
- [ ] Video 3–5 min coherente con el informe (3)
- [ ] Defensa oral ≤5 min: claridad y comprensión integral — **individual** (7)
- [ ] README completo con instrucciones de instalación y arranque
- [ ] Guía de estudio ensamblada desde las bitácoras de todos

> En la rúbrica original los sub-ítems de la Fase 7 suman 15 pero el encabezado dice
> 40. Asumí que informe/video/defensa pesan más de lo listado y preparalos en serio.

---

## 4. Cómo entregar

Rama `fase7-informe-nicole` → PR a `develop`.
El `README.md` final solo lo editás vos (evita conflictos).
Mergeá al final, cuando el resto ya esté en `develop`.
