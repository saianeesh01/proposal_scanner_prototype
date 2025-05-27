import os
import csv
from flask import Flask, request, render_template, redirect, url_for, session
from dotenv import load_dotenv
from models import db, ProposalScan
from ocr_utils import extract_text_from_bytes
from faiss_utils import classify_document
from logger import log_scan
from llm_utils import summarize_proposal
from textract_s3_utils import (
    upload_to_s3, start_text_detection, get_job_result,
    analyze_if_needed, is_structured_page
)
from qualifier_rules import apply_heuristic_boosts
from models import ProposalScan

# --- App Setup ---
app = Flask(__name__)
load_dotenv()

app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///scans.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# --- Routes ---

@app.route("/dashboard")
def dashboard():
    proposals = ProposalScan.query.order_by(ProposalScan.created_at.desc()).all()
    return render_template("index.html", proposals=proposals)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files.get("document")
        scan_type = request.form.get("scan_type")

        if uploaded_file:
            file_bytes = uploaded_file.read()

            # Extract text
            if scan_type == "s3":
                s3_key = upload_to_s3(file_bytes, uploaded_file.filename)
                blocks = get_job_result(start_text_detection(s3_key))
                lines = [b['Text'] for b in blocks if b['BlockType'] == 'LINE']
                extracted_text = "\n".join(lines)
                form_fields = analyze_if_needed(s3_key) if is_structured_page(lines) else None
            else:
                extracted_text = extract_text_from_bytes(file_bytes)
                form_fields = None

            # Classification
            label, distance, used_keywords = classify_document(extracted_text)
            final_label, confidence, rule_flags = apply_heuristic_boosts(label, distance, extracted_text)
            summary = summarize_proposal(extracted_text) if label == "PROPOSAL" else None

            # Logging
            log_scan(uploaded_file.filename, extracted_text, label, distance, used_keywords)

            # Save to DB
            new_scan = ProposalScan(
                filename=uploaded_file.filename,
                prediction=f"{final_label} (confidence: {round(confidence, 2)})",
                summary=summary or "(No summary available)"
            )
            db.session.add(new_scan)
            db.session.commit()

            return redirect(url_for("results", scan_id=new_scan.id))

    proposals = ProposalScan.query.order_by(ProposalScan.created_at.desc()).all()
    return render_template("index.html", proposals=proposals)

@app.route("/results/<int:scan_id>")
def results(scan_id):
    result = ProposalScan.query.get_or_404(scan_id)
    return render_template(
        "results.html",
        prediction=result.prediction,
        summary=result.summary,
        rules=session.get("rules", {})  # <-- store rules from last scan in session
    )


# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)
