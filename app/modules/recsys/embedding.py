from typing import List
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    _instance = None
    _model = None

    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        # Singleton Pattern: We only want to load the heavy AI model ONCE.
        if EmbeddingService._model is None:
            print(f"🧠 Loading Local AI Model ({model_name})")
            EmbeddingService._model = SentenceTransformer(model_name)
            self.dimensions = 768
            print("✅ Model Loaded!")

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates a 768-dim vector embedding locally using HuggingFace.
        """
        if not text:
            return [0.0] * self.dimensions

        try:
            # Clean newlines to prevent model confusion
            clean_text = text.replace("\n", " ")
            
            # Generate embedding (returns numpy array)
            vector = EmbeddingService._model.encode(clean_text)
            
            # Convert to standard Python list for JSON/Database compatibility
            return vector.tolist()
            
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            return [0.0] * self.dimensions

# Export a global instance to be imported elsewhere
embedding_service = EmbeddingService()