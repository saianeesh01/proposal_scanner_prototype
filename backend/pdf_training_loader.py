import os
import numpy as np
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import pdfplumber
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Paths
pdf_dir = "pdfs"
index_path = "proposal_index.npz"

logger.debug(f"Loading model: all-MiniLM-L6-v2")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load existing index
if os.path.exists(index_path):
    logger.debug(f"Loading existing index from {index_path}")
    data = np.load(index_path, allow_pickle=True)
    embeddings = data["embeddings"]
    texts = list(data["texts"])
    labels = list(data["labels"])
    logger.debug(f"Loaded {len(texts)} existing documents")
else:
    logger.debug("No existing index found, creating new arrays")
    embeddings = np.empty((0, 384), dtype='float32')  # 384 for MiniLM
    texts = []
    labels = []

def extract_text_from_pdf(file_path):
    logger.debug(f"Extracting text from {file_path}")
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                logger.debug(f"Processing page {i+1}")
                page_text = page.extract_text() or ""
                text += page_text
        logger.debug(f"Extracted {len(text)} characters")
        return text.strip()
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {str(e)}")
        return ""

# Process all PDFs
new_texts = []
new_files = 0

for filename in os.listdir(pdf_dir):
    if filename.lower().endswith(".pdf"):
        filepath = os.path.join(pdf_dir, filename)
        logger.debug(f"Processing file: {filename}")
        text = extract_text_from_pdf(filepath)
        if text and text not in texts:
            new_texts.append(text)
            new_files += 1
            logger.debug(f"Added new text with {len(text)} characters")

# Encode and update index
if new_texts:
    logger.info(f"Found {new_files} new proposal PDFs")
    logger.debug("Encoding new texts...")
    new_embeddings = model.encode(new_texts)
    texts.extend(new_texts)
    labels.extend(["proposal"] * len(new_texts))
    updated_embeddings = np.vstack([embeddings, new_embeddings])
    logger.debug(f"Saving updated index with {len(texts)} total documents")
    np.savez(index_path, embeddings=updated_embeddings, texts=texts, labels=labels)
    logger.info("FAISS index updated successfully")
else:
    logger.info("No new unique PDFs found to add")
