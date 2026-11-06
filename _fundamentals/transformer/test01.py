from sentence_transformers import SentenceTransformer
from sentence_transformers import util

# Initialize the sentence transformer model with the specified pre-trained model
# all-MiniLM-L6-v2 is a compact and efficient model for generating sentence embeddings
# This model maps sentences to dense vector representations (embeddings) that capture semantic meaning
model = SentenceTransformer("all-MiniLM-L6-v2") 

sentences = [
    "I love programming",
    "I enjoy software development",
    "I like dancing"
]

# Encode the sentences into embeddings using the model
embeddings = model.encode(sentences)

# Calculate cosine similarity between all pairs of sentence embeddings
similarity = util.cos_sim(embeddings, embeddings)

# Print the cosine similarity matrix
print(similarity)

# Print the shape of the embeddings matrix
print(embeddings.shape)