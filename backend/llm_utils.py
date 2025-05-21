import requests

def summarize_proposal(text):
    prompt = f"""
You are a helpful legal assistant. Summarize the following immigration proposal and extract key information:

- 🧾 Services offered
- 📄 Forms mentioned (e.g., I-485, I-130)
- 💵 Legal fees or pricing
- 📋 Scope of engagement or representation
- 📅 Any proposed timeline or duration
- 📝 Additional notes or disclaimers (e.g., no attorney-client relationship yet)

Return the result as a **clear bullet-point summary**.

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
