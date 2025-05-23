from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# ✅ Add more PROPOSAL examples (legal proposal language)
proposals = [
    "This proposal outlines legal representation for your green card application.",
    "We will assist with Form I-130 and I-485 preparation and filing.",
    "Our immigration team will represent you in your asylum case.",
    "Attached is a proposal for legal services including scope and attorney fees.",
    "We propose to provide family-based immigration support including NVC filings.",
    "Legal service agreement for DACA renewal assistance is included below.",
    "Proposal for employer-sponsored visa application under H-1B category.",
    "The following document outlines scope of services and retainer fee for USCIS filing.",
    "This letter outlines our plan to support your adjustment of status case.",
    "Included in this proposal are attorney qualifications and timeline for filing."
]

# ✅ Add more NON-PROPOSAL examples (receipts, reminders, forms)
non_proposals = [
    "Your Form I-797 receipt notice has been generated by USCIS.",
    "Reminder: USCIS biometrics appointment scheduled for August 2.",
    "Document checklist for I-130 application.",
    "Form I-485 application instructions for the beneficiary.",
    "Travel document attached: round trip to Mexico.",
    "Fee payment receipt from USCIS service center.",
    "Court hearing rescheduled due to judge availability.",
    "Cover letter for evidence submission to the immigration court.",
    "Reminder: update your address with USCIS within 10 days.",
    "Medical exam results required before adjustment interview."
]

# Combine and label
texts = proposals + non_proposals
labels = ['proposal'] * len(proposals) + ['non_proposal'] * len(non_proposals)

# Load model and encode
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts, convert_to_numpy=True)

# Build FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Save to file
np.savez("proposal_index.npz", embeddings=embeddings, texts=texts, labels=labels)
