"""predictor.py — Inferencia con TorchScript.

Alejandro (Fase 3): implementá LandmarkPredictor.

CONTRATO (no cambiar la firma — Nicole la usa desde la API):
    class LandmarkPredictor:
        def __init__(self, model_path: str = "models/transfer_learning.pt"): ...
        def predict(self, image, k: int = 3) -> dict:
            # {"landmark_id": str, "confidence": float, "top_k": [(id, prob), ...]}
"""

# TODO (Alejandro): implementar LandmarkPredictor


class LandmarkPredictor:
    def __init__(self, model_path: str = "models/transfer_learning.pt"):
        raise NotImplementedError("Alejandro (Fase 3): implementá LandmarkPredictor.__init__()")

    def predict(self, image, k: int = 3) -> dict:
        raise NotImplementedError("Alejandro (Fase 3): implementá LandmarkPredictor.predict()")
