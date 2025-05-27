import re

proposal_keywords = [
    "request for proposals", "rfp", "proposal", "solicitation", "submission deadline",
    "scope of work", "deliverables", "contract award", "technical approach",
    "budget", "cost proposal", "funding", "requirements", "qualifications",
    "evaluation criteria", "statement of work"
]
def count_matched_keywords(text):
    text_lower = text.lower()
    return sum(1 for keyword in proposal_keywords if keyword in text_lower)

def contains_keywords(text):
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in proposal_keywords)

def starts_like_proposal(text, lines_to_check=10):
    lines = text.strip().splitlines()
    top = "\n".join(lines[:lines_to_check]).lower()
    return any(phrase in top for phrase in ["request for proposal", "solicitation", "invitation to bid"])


def mentions_submission(text):
    return "submit" in text.lower() and "deadline" in text.lower()

def has_structured_sections(text):
    pattern = r"\n\s*(scope of work|budget|timeline|evaluation criteria|deliverables|requirements)\s*\n"
    return bool(re.search(pattern, text.lower()))


def apply_heuristic_boosts(label, distance, text):
    keyword_hits = count_matched_keywords(text)
    keyword_boost = min(keyword_hits, 3) * 0.05
    structured_boost = 0.05 if has_structured_sections(text) else 0
    header_boost = 0.05 if starts_like_proposal(text) else 0
    submission_boost = 0.05 if mentions_submission(text) else 0

    total_boost = keyword_boost + structured_boost + header_boost + submission_boost
    confidence = 1 - distance + total_boost

    if confidence > 0.8:
        final_label = "PROPOSAL"
    elif confidence > 0.65:
        final_label = "MAYBE_PROPOSAL"
    else:
        final_label = "NON_PROPOSAL"

    explanation = {
        "keywords": f"{keyword_hits} hit(s)",
        "structure": "✅" if structured_boost else "❌",
        "header": "✅" if header_boost else "❌",
        "submission": "✅" if submission_boost else "❌"
    }

    return final_label, confidence, explanation
