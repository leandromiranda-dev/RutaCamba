"""metrics.py — Métricas de re-ID: top-1, top-k, mAP.

Leandro (Fase 2-A): implementá evaluate_reid con la variante correcta de mAP re-ID.

CONTRATO (no cambiar la firma):
    def evaluate_reid(query_set, gallery) -> dict: ...
    # devuelve {'top1': float, 'top5': float, 'map': float}
"""
import numpy as np
from scipy.spatial.distance import cdist

def evaluate_reid(query_set: dict, gallery: dict) -> dict:
    """Devuelve {'top1': float, 'top5': float, 'map': float}. mAP variante re-ID."""
    
    # 1. Aplanar la galería para procesar las distancias de forma matricial
    gallery_embs = []
    gallery_ids = []
    
    for identidad, embs in gallery.items():
        for emb in embs:
            gallery_embs.append(emb)
            gallery_ids.append(identidad)
            
    gallery_embs = np.array(gallery_embs)
    gallery_ids = np.array(gallery_ids)
    
    aps = []
    top1_hits = 0
    top5_hits = 0
    total_queries = 0
    
    # 2. Iterar sobre cada consulta (probe/query)
    for query_id, embs in query_set.items():
        for query_emb in embs:
            total_queries += 1
            
            # Calcular similitud coseno entre el query y TODA la galería
            # cdist requiere arrays 2D, así que encerramos query_emb en una lista
            distances = cdist([query_emb], gallery_embs, metric='cosine')[0]
            
            # Rankear: obtener los índices de la galería ordenados de menor a mayor distancia
            ranked_indices = np.argsort(distances)
            ranked_ids = gallery_ids[ranked_indices]
            
            # Crear un vector booleano donde True significa que la identidad coincide
            hits = (ranked_ids == query_id)
            
            # --- Cálculo de Top-1 y Top-5 ---
            if hits[0]:
                top1_hits += 1
            if np.any(hits[:5]):
                top5_hits += 1
                
            # --- Cálculo de Average Precision (AP) Variante Re-ID ---
            total_relevant = np.sum(hits)
            
            if total_relevant == 0:
                aps.append(0.0)
                continue
                
            ap = 0.0
            hits_count = 0
            
            for k, is_hit in enumerate(hits):
                if is_hit:
                    hits_count += 1
                    # P@k: Precisión en la posición k (k+1 porque enumeramos desde 0)
                    precision_at_k = hits_count / (k + 1)
                    ap += precision_at_k
                    
            ap /= total_relevant
            aps.append(ap)
            
    # 3. Promediar las métricas finales
    mAP = np.mean(aps) if aps else 0.0
    top1 = top1_hits / total_queries if total_queries > 0 else 0.0
    top5 = top5_hits / total_queries if total_queries > 0 else 0.0
    
    return {
        'top1': float(top1),
        'top5': float(top5),
        'map': float(mAP)
    }