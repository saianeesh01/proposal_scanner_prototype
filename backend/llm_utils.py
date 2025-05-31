import requests

def summarize_proposal(text, label=None, explanation=None):
    qualifier_info = ""
    if label:
        qualifier_info += f"\n\n---\nClassifier/Qualifier result: {label}\n"
    if explanation:
        qualifier_info += f"Qualifier explanation: {explanation}\n---\n"

    prompt = f"""
You are a helpful legal assistant. Summarize the following immigration proposal and extract key information:

- 🧾 Services offered
- 📄 Forms mentioned (e.g., I-485, I-130)
- 💵 Legal fees or pricing
- 📋 Scope of engagement or representation
- 📅 Any proposed timeline or duration
- 📝 Additional notes or disclaimers (e.g., no attorney-client relationship yet)

**Additionally:**
- Give 2-3 suggestions for improving the proposal or making it more complete/clear.
- Clearly state the main reasons why this document **is** a proposal, or why it **is not** a proposal. List the evidence or lack thereof (e.g., missing legal terms, missing forms, unclear scope, etc).
- Take into account the following classifier/qualifier result and explanation when making your assessment and suggestions. If the document is classified as "NON_PROPOSAL" or "MAYBE_PROPOSAL", explain specifically why, and what would need to change for it to become a valid proposal.

{qualifier_info}

Return the result as a **clear bullet-point summary** with sections for:
- Key Information
- Suggestions
- Reasoning (why it is or is not a proposal, referencing the classifier/qualifier result)

Document:
{text}
"""
    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "gemma:2b",
            "prompt": prompt,
            "stream": False
        })

        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    except Exception as e:
        return f"⚠️ Error generating summary: {e}"
