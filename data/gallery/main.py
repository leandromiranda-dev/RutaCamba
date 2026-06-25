@app.post("/api/verificar")
async def verificar_identidad(imagen: UploadFile = File(...)):
    """
    Recibe una imagen (File) enviada desde una interfaz externa, 
    la procesa temporalmente y devuelve el resultado en JSON.
    """
    # 1. Crear un archivo temporal seguro para guardar la imagen entrante
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        contenido = await imagen.read()
        temp_file.write(contenido)
        ruta_temporal = temp_file.name

    try:
        # 2. Procesar la imagen con el motor biométrico
        acceso_concedido, identidad, score = procesar_control_acceso(
            ruta_temporal, 
            usuarios_permitidos, 
            sistema_reconocimiento, 
            umbral_minimo=0.70
        )
        
        # 3. Formatear la respuesta JSON para la interfaz
        porcentaje_exacto = round(float(score) * 100, 2)
        
        if acceso_concedido:
            return {
                "status": "success", 
                "mensaje": "ACCESO CONCEDIDO", 
                "identidad": identidad, 
                "similitud": porcentaje_exacto
            }
        else:
            return {
                "status": "denied", 
                "mensaje": "ACCESO DENEGADO", 
                "identidad": identidad, 
                "similitud": porcentaje_exacto
            }
            
    finally:
        # 4. Limpieza: Borrar siempre la foto temporal para no llenar el disco del servidor
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)