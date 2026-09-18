from app.embedder import embed_texts


texts = [
    "Why do pigs need energy?",
    "Pigs need energy for maintenance, growth, and reproduction.",
    "The weather is sunny today."
]


embeddings = embed_texts(texts)

print("Number of texts:", len(texts))
print("Embedding shape:", embeddings.shape)
print("First embedding:")
print(embeddings[0][:10])