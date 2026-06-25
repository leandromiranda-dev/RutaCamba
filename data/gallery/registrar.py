import os
import torch
from biometria import MotorBiometrico

# Rutas
RUTA_GALERIA = os.path.join("data", "gallery")
ARCHIVO_BD = "embeddings_autorizados.pt"

if __name__ == "__main__":
    motor = MotorBiometrico()
    base_datos_rostros = {}

    print(f"Escaneando rostros autorizados en '{RUTA_GALERIA}'...")
    
    # Extraer características de cada foto
    for archivo in os.listdir(RUTA_GALERIA):
        if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
            nombre = os.path.splitext(archivo)[0]
            ruta_completa = os.path.join(RUTA_GALERIA, archivo)
            
            embedding = motor.obtener_embedding(ruta_completa)
            if embedding is not None:
                base_datos_rostros[nombre] = embedding
                print(f"✅ Vector biométrico extraído y guardado para: {nombre}")

    # Guardar el diccionario completo en el disco usando PyTorch
    torch.save(base_datos_rostros, ARCHIVO_BD)
    print(f"\n¡Proceso completado! Base de datos guardada en el archivo '{ARCHIVO_BD}'")