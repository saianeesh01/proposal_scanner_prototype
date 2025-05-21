import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Load existing dataset
data = np.load("proposal_index.npz", allow_pickle=True)
embeddings = data["embeddings"]
texts = list(data["texts"])
labels = list(data["labels"])

# New proposal samples (paste your cleaned texts here)
new_texts = [
    """Request for Proposals Immigration Legal Services The purpose of this RFP is for the George Washington Regional Commission (GWRC) to solicit proposals to establish a single contract from a qualified source to provide professional immigration legal services. This contract is through competitive negotiation and seeks a provider who can assist the region with immigration cases, outreach, and legal guidance to immigrant populations. Proposals must comply with all specified requirements, including terms, submission guidelines, and service qualifications.""",

    """Congressional Research Service Report: Permanent Legal Immigration to the United States. U.S. immigration policy is based on four major principles: family reunification, admitting needed skilled workers, providing humanitarian protection, and promoting diversity. Legal permanent residents (LPRs) include those granted immigrant visas through family-based, employment-based, and humanitarian programs. The annual worldwide cap is 675,000, though some categories like immediate relatives and asylees are not numerically limited. The INA provides further special immigrant visas and humanitarian statuses.""",

    """West Virginia Attorney General RFP: Glenville State College is seeking legal representation for immigration-related matters involving students and employees. Required services include assistance with H-1B petitions, permanent residency (PERM, I-140, I-485), and counseling for J-1, TN, and other visa types. The selected attorney will coordinate with general counsel, HR, and stakeholders to provide legal advice and filings. Proposals should outline immigration law expertise and experience working with higher education institutions.""",

    """City of Austin RFP: Immigration Legal Services Scope of Work. The city seeks qualified legal service providers to offer representation, education, and resources to immigrants, including detainees. Services include legal representation and advocacy by qualified attorneys, outreach, and assistance navigating the immigration system. Proposals must demonstrate experience working with immigrant populations, knowledge of removal defense, and community-based service delivery. Funding is available for outreach, legal navigation, and direct legal aid.""",

    """Congressional Research Report R42866: This document provides an overview of the INA and permanent legal immigration categories. It explains pathways like employment-based visas, refugee and asylee programs, and family-sponsored categories. It emphasizes the policy goals of economic need, family unity, and humanitarian protection. The report also touches on the number of immigrants admitted annually and the policy mechanisms through which U.S. immigration law is implemented.""",
    
    """IMMIGRATION LAW CLINIC PROPOSAL Submitted by: Dean Melanie B. Jacobs, University of Louisville. This proposal requests $240,000/year to support an Immigration Law Clinic providing legal services to parolees and immigrants in Kentucky. Services include EAD application assistance, parole extensions, and representation in hearings. Students will receive hands-on training under a licensed immigration attorney. A two-week legal boot camp precedes fieldwork. The proposal includes a 5-year projected budget covering salary, benefits, operational costs, and filing fees. The clinic aims to improve immigration legal access and create a pipeline of immigration attorneys while benefiting the Commonwealth's economy."""

]


new_labels = ["proposal"] * len(new_texts)

# Load model and encode
model = SentenceTransformer("all-MiniLM-L6-v2")
new_embeddings = model.encode(new_texts)

# Update dataset
updated_embeddings = np.vstack([embeddings, new_embeddings])
texts.extend(new_texts)
labels.extend(new_labels)

# Save updated index
np.savez("proposal_index.npz", embeddings=updated_embeddings, texts=texts, labels=labels)
print("✅ FAISS index updated with 6 new immigration proposals.")  