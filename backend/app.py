import os
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
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
import logging
from werkzeug.exceptions import BadRequest, NotFound
import threading

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Setup ---
app = Flask(__name__)
load_dotenv()

app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///scans.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()

def chunk_text(text, chunk_size=2000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def generate_summary_async(scan_id, extracted_text, label=None, explanation=None):
    from llm_utils import summarize_proposal
    from models import db, ProposalScan
    # Split into chunks for more complete summaries
    chunks = chunk_text(extracted_text, chunk_size=2000, overlap=200)
    chunk_summaries = []
    for chunk in chunks:
        chunk_summary = summarize_proposal(chunk, label=label, explanation=explanation)
        chunk_summaries.append(chunk_summary)
    combined_summary = "\n\n".join(chunk_summaries)
    with app.app_context():
        scan = ProposalScan.query.get(scan_id)
        if scan:
            scan.summary = combined_summary
            db.session.commit()

# --- Error Handlers ---
@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"404 error: {error}")
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    db.session.rollback()
    return render_template("500.html"), 500

# --- Routes ---

@app.route("/", methods=["GET", "POST"])
def index():
    try:
        if request.method == "POST":
            uploaded_file = request.files.get("document")
            scan_type = request.form.get("scan_type")

            if not uploaded_file:
                logger.warning("No file uploaded")
                raise BadRequest("No file uploaded")

            logger.debug(f"Processing file: {uploaded_file.filename}")
            file_bytes = uploaded_file.read()

            # Extract text
            try:
                if scan_type == "s3":
                    logger.debug("Using S3/Textract processing")
                    s3_key = upload_to_s3(file_bytes, uploaded_file.filename)
                    blocks = get_job_result(start_text_detection(s3_key))
                    lines = [b['Text'] for b in blocks if b['BlockType'] == 'LINE']
                    extracted_text = "\n".join(lines)
                    form_fields = analyze_if_needed(s3_key) if is_structured_page(lines) else None
                else:
                    logger.debug("Using local OCR processing")
                    extracted_text = extract_text_from_bytes(file_bytes)
                    form_fields = None
            except Exception as e:
                logger.error(f"Text extraction failed: {str(e)}")
                raise

            # Classification
            logger.debug("Classifying document")
            label, distance, used_keywords = classify_document(extracted_text)
            final_label, confidence, rule_flags = apply_heuristic_boosts(label, distance, extracted_text)

            # Logging
            log_scan(uploaded_file.filename, extracted_text, label, distance, used_keywords)

            # Save to DB (summary is set to None for now)
            try:
                new_scan = ProposalScan(
                    filename=uploaded_file.filename,
                    prediction=f"{final_label} (confidence: {round(confidence, 2)})",
                    label=final_label,
                    summary=None
                )
                db.session.add(new_scan)
                db.session.commit()
                logger.info(f"Saved scan {new_scan.id} to database")
            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                db.session.rollback()
                raise

            # Start summary generation in background, passing label and explanation
            threading.Thread(
                target=generate_summary_async,
                args=(new_scan.id, extracted_text, final_label, rule_flags),
                daemon=True
            ).start()

            session['rules'] = rule_flags
            return redirect(url_for("results", scan_id=new_scan.id))

        proposals = ProposalScan.query.order_by(ProposalScan.created_at.desc()).all()
        return render_template("index.html", proposals=proposals)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/dashboard")
def dashboard():
    proposals = ProposalScan.query.order_by(ProposalScan.created_at.desc()).all()
    return render_template("index.html", proposals=proposals)

@app.route("/results/<int:scan_id>")
def results(scan_id):
    result = ProposalScan.query.get_or_404(scan_id)
    summary_ready = bool(result.summary and result.summary.strip())
    return render_template(
        "results.html",
        prediction=result.prediction,
        summary=result.summary,
        summary_ready=summary_ready,
        rules=session.get("rules", {})
    )

@app.route("/delete/<int:scan_id>", methods=["POST"])
def delete_scan(scan_id):
    try:
        scan = ProposalScan.query.get_or_404(scan_id)
        logger.info(f"Deleting scan {scan_id}")
        db.session.delete(scan)
        db.session.commit()
        return redirect(url_for("dashboard"))
    except NotFound:
        logger.error(f"Scan {scan_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error deleting scan {scan_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# --- Run ---
if __name__ == "__main__":
    app.run(debug=True)
