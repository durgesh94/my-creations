
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Step 1: Sample sentences
sentences = [
    "Patients can cancel appointments up to 24 hours before the scheduled appointment.",
    "Cancellations made less than 24 hours before the appointment may incur charges.",
    "Patients must pay consultation fees before meeting the doctor.",
    "Patients can pay their consultation fees using cash, card or UPI."
]

# Step 2: Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Step 3: Generate embeddings
embeddings = model.encode(sentences)

print("Number of sentences:", len(sentences))
print("Embedding shape:", embeddings.shape)

# Step 4: Compare consecutive sentences
print("\n--- Semantic Similarity ---")

for i in range(len(sentences) - 1):

    similarity = cosine_similarity(
        [embeddings[i]],
        [embeddings[i + 1]]
    )[0][0]

    print(f"\nSentence {i + 1} vs Sentence {i + 2}")
    print(f"Similarity: {similarity:.4f}")
