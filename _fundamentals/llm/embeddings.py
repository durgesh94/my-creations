from sentence_transformers import SentenceTransformer

# Load a pretrained embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

sentences = [
    "I love programming",
    "I enjoy coding",
    "I like dancing",
    "I love Python"
]

# Generate embeddings
embeddings = model.encode(sentences)

# Display results
for sentence, embedding in zip(sentences, embeddings):
    print("\nSentence:", sentence)
    print("Embedding:", embedding)
    print("Dimensions:", len(embedding))