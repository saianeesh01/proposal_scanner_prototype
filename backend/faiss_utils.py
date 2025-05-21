import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Load index from file
data = np.load("proposal_index.npz", allow_pickle=True)
embeddings = data["embeddings"]
texts = data["texts"]
labels = data["labels"]

# Build FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Load transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

KEYWORDS = ["proposal", "funding", "budget", "support", "request"]

def keyword_boost(text):
    return any(word in text.lower() for word in KEYWORDS)

def classify_document(text, top_k=1):
    query_embedding = model.encode([text], convert_to_numpy=True)
    distances, indices = index.search(query_embedding, top_k)
    distance = distances[0][0]

    has_keywords = keyword_boost(text)

    if distance < 0.60:
        label = "PROPOSAL"
    elif distance < 0.68 or (has_keywords and distance < 0.73):
        label = "MAYBE_PROPOSAL"
    elif distance < 0.78:
        label = "NEEDS REVIEW"
    else:
        label = "NON_PROPOSAL"

    return label, distance, has_keywords



