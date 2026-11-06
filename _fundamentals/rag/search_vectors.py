import chromadb

from sentence_transformers import SentenceTransformer

# 1. Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Connect to existing ChromaDB
client = chromadb.PersistentClient(
    path="./chroma_db"
)

# 3. Get existing collection
collection = client.get_collection(
    name="hams_hospital_policies"
)

# 4. User query
query = "Can I cancel my appointment one day before?"

# 5. Generate query embedding
query_embedding = model.encode(query)

# 6. Search vector database
results = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=3
)

# 7. Display results
for index, document in enumerate(results["documents"][0]):

    print(f"\nResult {index + 1}")

    print("Document:", document)

    print("Distance:", results["distances"][0][index])

    print("Metadata:", results["metadatas"][0][index])