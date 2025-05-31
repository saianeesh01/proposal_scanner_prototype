import numpy as np
from sentence_transformers import SentenceTransformer 
import faiss 
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load index from file
logger.debug("Loading FAISS index from file")
data = np.load("proposal_index.npz", allow_pickle=True)
embeddings = data["embeddings"]
texts = data["texts"]
labels = data["labels"]
logger.debug(f"Loaded index with {len(texts)} documents")

# Build FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)
logger.debug(f"Built FAISS index with dimension {dimension}")

# Load transformer model
logger.debug("Loading transformer model")
model = SentenceTransformer('all-MiniLM-L6-v2')

KEYWORDS = ["proposal", "funding", "budget", "support", "request"]

def keyword_boost(text):
    return any(word in text.lower() for word in KEYWORDS)

def classify_document(text, top_k=1):
    logger.debug(f"Classifying document with length {len(text)}")
    query_embedding = model.encode([text], convert_to_numpy=True)
    distances, indices = index.search(query_embedding, top_k)
    distance = distances[0][0]
    
    has_keywords = keyword_boost(text)
    logger.debug(f"Distance: {distance:.3f}, Has keywords: {has_keywords}")

    if distance < 0.60:
        label = "PROPOSAL"
    elif distance < 0.68 or (has_keywords and distance < 0.73):
        label = "MAYBE_PROPOSAL"
    elif distance < 0.78:
        label = "NEEDS REVIEW"
    else:
        label = "NON_PROPOSAL"
    
    logger.debug(f"Classified as: {label}")
    return label, distance, has_keywords



