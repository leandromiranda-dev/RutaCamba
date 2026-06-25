"""embeddings.py — Embeddings faciales con DeepFace/ArcFace.

Leandro (Fase 2-A): implementá get_embedding y build_gallery.

CONTRATO (no cambiar las firmas):
    def get_embedding(image) -> np.ndarray: ...
    def build_gallery(gallery_dir: str) -> dict: ...
"""
import os
import torch
import numpy as np
from deepface import DeepFace

def get_embedding(image) -> np.ndarray:
    """Vector de embedding del rostro (DeepFace/ArcFace). Devuelve None si no detecta rostro."""
    try:
        # enforce_detection=True obliga a DeepFace a lanzar un ValueError si no ve a nadie.
        resultados = DeepFace.represent(
            img_path=image, 
            model_name="ArcFace", 
            enforce_detection=True
        )
        
        # Extraemos el vector del primer rostro detectado y lo convertimos a numpy array
        embedding = resultados[0]['embedding']
        return np.array(embedding)
        
    except ValueError:
        return None
    except Exception as e:
        print(f"Error inesperado procesando la imagen: {e}")
        return None

def build_gallery(gallery_dir: str) -> dict:
    """{identidad: [emb, emb, ...]} leyendo imágenes directamente desde gallery_dir."""
    cache_path = os.path.join(gallery_dir, "embeddings_autorizados.pt")
    
    # 1. Cargar desde la caché si ya existe
    if os.path.exists(cache_path):
        print(f"Cargando galería cacheada desde {cache_path}...")
        return torch.load(cache_path, weights_only=False)
            
    # 2. Si no hay caché, procesar las fotos sueltas
    print("Construyendo galería de embeddings desde cero...")
    gallery = {}
    
    for archivo in os.listdir(gallery_dir):
        # Filtramos para procesar solo imágenes
        if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(gallery_dir, archivo)
            
            # El nombre del archivo (sin el .jpg) será la identidad
            identidad = os.path.splitext(archivo)[0]
            
            emb = get_embedding(img_path)
            
            if emb is not None:
                # Lo guardamos dentro de una lista [emb] para cumplir con el contrato del equipo
                gallery[identidad] = [emb]
                print(f"✅ Procesado: {identidad}")
            else:
                print(f"⚠️ Advertencia: No se detectó rostro en {archivo}")
            
    # 3. Guardar el archivo .pt
    torch.save(gallery, cache_path)
    print(f"\n¡Galería guardada exitosamente en {cache_path}!")
        
    return gallery