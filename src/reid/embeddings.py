"""embeddings.py — Embeddings faciales con DeepFace/ArcFace.

Leandro (Fase 2-A): implementá get_embedding y build_gallery.

CONTRATO (no cambiar las firmas):
    def get_embedding(image) -> np.ndarray: ...
    def build_gallery(gallery_dir: str) -> dict: ...
"""
import os
import pickle
import numpy as np
from deepface import DeepFace

def get_embedding(image) -> np.ndarray:
    """Vector de embedding del rostro (DeepFace/ArcFace). Devuelve None si no detecta rostro."""
    try:
        # DeepFace.represent devuelve una lista de diccionarios (uno por rostro).
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
        # Manejo del caso "no se detectó rostro" estipulado en tus requerimientos
        return None
    except Exception as e:
        print(f"Error inesperado procesando la imagen: {e}")
        return None

def build_gallery(gallery_dir: str) -> dict:
    """{identidad: [emb, emb, ...]} a partir de carpetas por persona."""
    cache_path = os.path.join(gallery_dir, "gallery_embeddings.pkl")
    
    # 1. Intentamos cargar desde la caché para no recalcular
    if os.path.exists(cache_path):
        print(f"Cargando galería cacheados desde {cache_path}...")
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
            
    # 2. Si no hay caché, construimos la galería leyendo las carpetas
    print("Construyendo galería de embeddings desde cero...")
    gallery = {}
    
    # Asumimos que la estructura es: data/gallery/<persona>/<imagen>.jpg
    for identidad in os.listdir(gallery_dir):
        identidad_path = os.path.join(gallery_dir, identidad)
        
        if not os.path.isdir(identidad_path):
            continue
            
        embeddings_persona = []
        for img_name in os.listdir(identidad_path):
            # Filtramos para leer solo archivos de imagen
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(identidad_path, img_name)
                emb = get_embedding(img_path)
                
                if emb is not None:
                    embeddings_persona.append(emb)
                else:
                    print(f"Advertencia: No se detectó ningún rostro en {img_path}")
        
        # Solo agregamos a la persona si logramos extraer al menos un embedding
        if embeddings_persona:
            gallery[identidad] = embeddings_persona
            
    # 3. Guardamos la galería calculada en un archivo .pkl
    with open(cache_path, 'wb') as f:
        pickle.dump(gallery, f)
        
    return gallery