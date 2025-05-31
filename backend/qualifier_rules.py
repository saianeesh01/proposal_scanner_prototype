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

    # Dynamic, detailed explanation
    explanation = {}
    # Header
    if header_boost:
        explanation["header"] = "✅ Starts with a typical proposal header."
    else:
        explanation["header"] = "❌ Does not start with a typical proposal header (e.g., 'Request for Proposal', 'Solicitation', 'Invitation to Bid')."
    # Keywords
    if keyword_hits >= 3:
        explanation["keywords"] = f"✅ Contains {keyword_hits} proposal-related keywords."
    elif keyword_hits > 0:
        explanation["keywords"] = f"⚠️ Only {keyword_hits} proposal-related keyword(s) found."
    else:
        explanation["keywords"] = "❌ No proposal-related keywords found."
    # Structure
    if structured_boost:
        explanation["structure"] = "✅ Has structured sections (e.g., Scope of Work, Budget, Timeline, etc.)."
    else:
        explanation["structure"] = "❌ Missing clear structured sections (Scope of Work, Budget, etc.)."
    # Submission
    if submission_boost:
        explanation["submission"] = "✅ Mentions submission and deadline."
    else:
        explanation["submission"] = "❌ Does not mention submission instructions or deadline."

    # Add actionable suggestions
    suggestions = []
    if not header_boost:
        suggestions.append("Add a clear proposal header, such as 'Request for Proposal' or 'Solicitation'.")
    if keyword_hits < 3:
        suggestions.append("Include more proposal-related keywords (e.g., 'scope of work', 'budget', 'evaluation criteria').")
    if not structured_boost:
        suggestions.append("Add structured sections like 'Scope of Work', 'Budget', or 'Timeline'.")
    if not submission_boost:
        suggestions.append("Specify submission instructions and a deadline.")
    if not suggestions:
        suggestions.append("No major issues detected. Document structure looks like a proposal.")
    explanation["suggestions"] = suggestions

    return final_label, confidence, explanation
