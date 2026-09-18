from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def embed_texts(texts):
    """Convert a list of texts into embedding vectors."""

    embeddings = model.encode(
        texts,
        normalize_embeddings=True
    )

    return embeddings