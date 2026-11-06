from sentence_transformers import SentenceTransformer
from chunking import chunk_text

# 1. Load document
with open("documents/hospital_policy.txt", "r") as file:
    document = file.read()

# 2. Generate chunks
chunks = chunk_text(document)

# 3. Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 4. Generate embeddings
embeddings = model.encode(chunks)

# 5. Display results
print("Total chunks:", len(chunks))
print("Embedding shape:", embeddings.shape)

for index, chunk in enumerate(chunks):

    print(f"\nChunk {index + 1}:")
    print(chunk)

    print("Embedding dimensions:", len(embeddings[index]))
    print("First 5 vector values:", embeddings[index][:5])