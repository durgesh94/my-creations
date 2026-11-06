import chromadb

from sentence_transformers import SentenceTransformer
from chunking import chunk_text

# 1. Read document
with open("documents/hospital_policy.txt", "r") as file:
    document = file.read()

# 2. Generate chunks
chunks = chunk_text(document)

# 3. Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 4. Generate embeddings
embeddings = model.encode(chunks)

# 5. Initialize persistent ChromaDB
client = chromadb.PersistentClient(
    path="./chroma_db"
)

# 6. Create collection
collection_name = "hams_hospital_policies"

try:
    client.delete_collection(name=collection_name)
except Exception:
    pass

collection = client.create_collection(name=collection_name)

# 7. Store chunks and embeddings
collection.upsert(
    ids=[f"policy_{i}" for i in range(len(chunks))],
    documents=chunks,
    embeddings=embeddings.tolist(),
    metadatas=[
        {
            "source": "hospital_policy.txt",
            "chunk_number": i
        }
        for i in range(len(chunks))
    ]
)

print("Successfully stored embeddings!")
print("Total records:", collection.count())