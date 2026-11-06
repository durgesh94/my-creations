import os
import chromadb

from dotenv import load_dotenv
from google import genai
from sentence_transformers import SentenceTransformer

# 1. Load environment variables
load_dotenv()

# 2. Initialize Gemini
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# 3. Load embedding model
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# 4. Connect to ChromaDB
chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_collection(
    name="hams_hospital_policies"
)

# 5. Receive user question
question = "Can I cancel my appointment one day before?"

# 6. Generate query embedding
query_embedding = embedding_model.encode(question)

# 7. Retrieve relevant documents
results = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=3
)

# 8. Prepare retrieved context
context = "\n\n".join(
    results["documents"][0]
)

# 9. Construct prompt
prompt = f"""
You are a helpful hospital assistant.

Answer the user's question using ONLY the
provided hospital policy context.

If the answer is not available in the context,
say that you do not have enough information.

Do not invent hospital policies.

Hospital Policy Context:
{context}

User Question:
{question}

Provide a clear and concise answer.
"""

# 10. Send prompt to Gemini
response = client.models.generate_content(
    model="gemini-3.5-flash", # gemini 3.5 flash model
    contents=prompt
)

# 11. Display answer
print("\nUser Question:")
print(question)

print("\nRetrieved Context:")
print(context)

print("\nGenerated Answer:")
print(response.text)