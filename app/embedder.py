from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer


# =========================================================
# CONFIGURATION
# =========================================================

MODEL_NAME = "all-MiniLM-L6-v2"


# =========================================================
# MODEL LOADER
# =========================================================

@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the sentence-transformer model once per Python
    process and reuse it for all subsequent embedding calls.
    """

    return SentenceTransformer(
        MODEL_NAME
    )


# =========================================================
# EMBEDDING
# =========================================================

def embed_texts(
    texts
):
    """
    Convert a list of texts into normalized embedding vectors.

    The model is loaded once and reused.
    """

    if not texts:
        return np.empty(
            (0, 0),
            dtype=np.float32
        )

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
        batch_size=32
    )

    return np.asarray(
        embeddings,
        dtype=np.float32
    )