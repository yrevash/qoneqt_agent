from typing import List
import os
import shutil
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    _instance = None
    _model = None

    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        # Singleton Pattern: We only want to load the heavy AI model ONCE.
        if EmbeddingService._model is None:
            print(f"Loading Local AI Model ({model_name})")
            try:
                EmbeddingService._model = SentenceTransformer(model_name)
                self.dimensions = 768
                print("Model Loaded!")
            except Exception as e:
                print(f"Error loading model, clearing cache and retrying: {e}")
                # Clear corrupted cache
                cache_dir = os.path.expanduser("~/.cache/torch/sentence_transformers")
                if os.path.exists(cache_dir):
                    print(f"Clearing cache at {cache_dir}")
                    shutil.rmtree(cache_dir, ignore_errors=True)
                # Retry download
                print(f" Re-downloading model: {model_name}")
                EmbeddingService._model = SentenceTransformer(model_name)
                self.dimensions = 768
                print(" Model Loaded!")

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates a 768-dim vector embedding locally using HuggingFace.
        """
        if not text:
            return [0.0] * self.dimensions

        try:
            clean_text = text.replace("\n", " ")
            vector = EmbeddingService._model.encode(clean_text)          
            return vector.tolist()
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * self.dimensions

# Export a global instance to be imported elsewhere
embedding_service = EmbeddingService()