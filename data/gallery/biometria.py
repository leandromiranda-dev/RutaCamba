import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from scipy.spatial.distance import cosine
from PIL import Image

class MotorBiometrico:
    def __init__(self):
        """Inicializa los modelos de detección de rostros y extracción de embeddings."""
        # MTCNN se encarga de localizar y recortar de forma óptima el rostro
        self.mtcnn = MTCNN(image_size=160, margin=0, min_face_size=20)
        # InceptionResnetV1 procesa el recorte y extrae el vector numérico (embedding) de 512 dimensiones
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval()

    def obtener_embedding(self, ruta_imagen):
        """Detecta un rostro en la imagen dada y devuelve su embedding como un array de numpy."""
        try:
            img = Image.open(ruta_imagen).convert('RGB')
        except Exception as e:
            print(f"Error al abrir el archivo {ruta_imagen}: {e}")
            return None

        # Detectar y extraer el rostro de la imagen
        cara_recortada = self.mtcnn(img)
        
        if cara_recortada is None:
            print(f"No se detectó ningún rostro visible en: {ruta_imagen}")
            return None
            
        # Añadir la dimensión del lote (batch dimension) requerida por PyTorch
        cara_recortada = cara_recortada.unsqueeze(0)
        
        with torch.no_grad():
            embedding = self.resnet(cara_recortada)
            
        # Retornar como un vector plano de NumPy para facilitar el cálculo matemático posterior
        return embedding.squeeze().numpy()

    def calcular_similitud_coseno(self, embedding1, embedding2):
        """Calcula el porcentaje de similitud basado en la distancia coseno."""
        distancia = cosine(embedding1, embedding2)
        # La similitud coseno es el complemento de la distancia coseno
        return 1 - distancia