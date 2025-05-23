import csv
from flask import Flask, request, render_template, redirect, url_for
from ocr_utils import extract_text_from_bytes
from faiss_utils import classify_document
from logger import log_scan
from llm_utils import summarize_proposal
from textract_s3_utils import upload_to_s3, start_text_detection, get_job_result, analyze_if_needed, is_structured_page

app = Flask(__name__)

@app.route("/dashboard")
def dashboard():
    proposals = [
        {"id": 12345, "client": "Acme Corp", "date": "2023-08-15", "status": "Pending"},
        {"id": 67890, "client": "Global Innovations", "date": "2023-07-22", "status": "Approved"},
        # ...more rows
    ]
    return render_template("index.html", proposals=proposals)

@app.route("/", methods=["GET", "POST"])
def index():
    extracted_text = None
    prediction = None
    summary = None
    form_fields = None
    used_keywords = False  # ✅ Set default

    if request.method == "POST":
        uploaded_file = request.files.get("document")
        scan_type = request.form.get("scan_type")

        if uploaded_file:
            file_bytes = uploaded_file.read()

            if scan_type == "s3":
                # ✅ Hybrid S3 flow
                s3_key = upload_to_s3(file_bytes, uploaded_file.filename)
                blocks = get_job_result(start_text_detection(s3_key))
                lines = [b['Text'] for b in blocks if b['BlockType'] == 'LINE']
                extracted_text = "\n".join(lines)

                if is_structured_page(lines):
                    form_fields = analyze_if_needed(s3_key)

                label, distance, used_keywords = classify_document(extracted_text)
                prediction = f"{label.upper()} (distance: {round(distance, 2)})"


            else:
                # ✅ Local flow with FAISS + classifier
                extracted_text = extract_text_from_bytes(file_bytes)
                label, distance, used_keywords = classify_document(extracted_text)
                prediction = f"{label.upper()} (distance: {round(distance, 2)})"
            # After extracting text and classifying
            if label == "PROPOSAL":
                summary = summarize_proposal(extracted_text)
            # ✅ Log results
            log_scan(uploaded_file.filename, extracted_text, label, distance, used_keywords)

    return render_template(
    "index.html",
    text=extracted_text,
    prediction=prediction,
    summary=summary,
    form_fields=form_fields,
    used_keywords=used_keywords,
    #proposals=proposals  # Optional if you want to load the table dynamically
)


if __name__ == "__main__":
    app.run(debug=True)
