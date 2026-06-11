# Diseño de la CNN desde cero (B1) — "en papel"

**Tarea:** clasificar 8 landmarks de Santa Cruz a partir de imágenes RGB 224×224.
**Requisitos del enunciado:** ≥3 capas convolucionales, pooling, BatchNorm, dropout, capas fully-connected. Test accuracy ≥ 45%.

## Arquitectura: `TuristCNN`

```
Entrada: 3 × 224 × 224
│
├─ Bloque 1: Conv 3×3 (3→32)   + BatchNorm + ReLU + MaxPool 2×2   → 32 × 112 × 112
├─ Bloque 2: Conv 3×3 (32→64)  + BatchNorm + ReLU + MaxPool 2×2   → 64 × 56 × 56
├─ Bloque 3: Conv 3×3 (64→128) + BatchNorm + ReLU + MaxPool 2×2   → 128 × 28 × 28
├─ Bloque 4: Conv 3×3 (128→256)+ BatchNorm + ReLU + MaxPool 2×2   → 256 × 14 × 14
│
├─ AdaptiveAvgPool2d(1)                                            → 256
├─ Dropout(0.5)
├─ FC 256 → 128 + ReLU
├─ Dropout(0.3)
└─ FC 128 → 8 (logits)
```

**Parámetros totales: ~430K** (vs ~11M de ResNet18 — dato para la tabla comparativa B1 vs B2).

## Justificación de cada decisión

| Decisión | Por qué |
|---|---|
| **4 bloques conv (supera el mínimo de 3)** | Con 3 bloques el mapa final es 28×28, demasiado grande y con poca abstracción; 4 bloques dan campo receptivo suficiente para rasgos de landmarks (torres, fachadas, vegetación) sin inflar parámetros. |
| **Canales 32→64→128→256 (duplicar al reducir resolución)** | Patrón estándar: al perder resolución espacial se compensa con más canales; mantiene el costo por capa aproximadamente constante. |
| **Kernels 3×3, padding 1** | Dos 3×3 apilados cubren lo mismo que un 5×5 con menos parámetros y más no-linealidad (lección de VGG). |
| **BatchNorm tras cada conv** | Estabiliza y acelera el entrenamiento (permite lr más alto) y regulariza ligeramente; crítico al entrenar desde cero con un dataset pequeño (~800 imágenes). |
| **MaxPool 2×2** | Reducción espacial simple y eficaz; invarianza local a traslación (las fotos vienen de ángulos y distancias variadas). |
| **AdaptiveAvgPool(1) en vez de Flatten** | Reduce 256×14×14 → 256: la FC pasa de ~50M de pesos (flatten) a 33K. Menos overfitting y la red acepta otros tamaños de entrada. |
| **Dropout 0.5 / 0.3 en la cabeza** | Las FC son las que más memorizan; con dataset pequeño el dropout es la defensa principal contra overfitting (junto con augmentation). |
| **ReLU** | Estándar, barato, sin saturación de gradientes. |

## Entrenamiento

| Componente | Elección | Por qué |
|---|---|---|
| Pérdida | CrossEntropyLoss | Clasificación multiclase de 8 clases; opción `weight` por clase si el EDA muestra desbalance. |
| Optimizador | Adam, lr = 1e-3, weight decay = 1e-4 | Converge rápido sin tuning fino; weight decay como regularización extra. |
| Scheduler | ReduceLROnPlateau (factor 0.5, paciencia 3, sobre val loss) | Baja el lr cuando la validación se estanca; simple de justificar. |
| Épocas | ≥ 30 (requisito) con early-stopping implícito: se guarda solo el mejor checkpoint por **menor val loss** | El test no se toca hasta el final (regla de oro). |
| Batch size | 32 | Equilibrio memoria/estabilidad de BatchNorm; si se cambia, ajustar lr en proporción (relación batch size ↔ lr, pregunta de defensa). |

## Detección de overfitting (pregunta de defensa)

Las curvas train/val de loss y accuracy se loggean por época en WandB. Señal de overfitting: train loss sigue bajando mientras val loss sube. Mitigación en esta red: augmentation moderado (solo train), dropout, weight decay, BatchNorm y checkpoint por mejor val loss.
