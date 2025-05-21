import os
import numpy as np
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import pdfplumber

# Paths
pdf_dir = "pdfs"
index_path = "proposal_index.npz"

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load existing index
if os.path.exists(index_path):
    data = np.load(index_path, allow_pickle=True)
    embeddings = data["embeddings"]
    texts = list(data["texts"])
    labels = list(data["labels"])
else:
    embeddings = np.empty((0, 384), dtype='float32')  # 384 for MiniLM
    texts = []
    labels = []

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()

# Process all PDFs
new_texts = []
new_files = 0

for filename in os.listdir(pdf_dir):
    if filename.lower().endswith(".pdf"):
        filepath = os.path.join(pdf_dir, filename)
        text = extract_text_from_pdf(filepath)
        if text and text not in texts:
            new_texts.append(text)
            new_files += 1

# Encode and update index
if new_texts:
    print(f"📄 Found {new_files} new proposal PDFs")
    new_embeddings = model.encode(new_texts)
    texts.extend(new_texts)
    labels.extend(["proposal"] * len(new_texts))
    updated_embeddings = np.vstack([embeddings, new_embeddings])
    np.savez(index_path, embeddings=updated_embeddings, texts=texts, labels=labels)
    print("✅ FAISS index updated.")
else:
    print("ℹ️ No new unique PDFs found to add.")
