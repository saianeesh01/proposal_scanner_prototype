from textract_s3_utils import upload_to_s3, start_text_detection, get_job_result, is_structured_page, analyze_if_needed

def run_textract_pipeline(file_path):
    # Step 1: Read the file
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    print("📤 Uploading to S3...")
    s3_key = upload_to_s3(file_bytes, file_path.split("/")[-1])
    print("✅ Uploaded as:", s3_key)

    print("🧠 Starting DetectDocumentText async job...")
    job_id = start_text_detection(s3_key)

    print("⏳ Waiting for Textract to finish...")
    blocks = get_job_result(job_id)

    print("\n--- Raw Text (First 10 lines) ---")
    lines = [b['Text'] for b in blocks if b['BlockType'] == 'LINE']
    for line in lines[:10]:
        print(line)

    if is_structured_page(lines):
        print("\n⚙️ Detected structured format — running AnalyzeDocument...")
        form_fields = analyze_if_needed(s3_key)
        print("\n--- Extracted Key-Value Pairs ---")
        for k, v in form_fields:
            print(f"{k} : {v}")
    else:
        print("\n✅ No structured content found — skipping AnalyzeDocument.")

if __name__ == "__main__":
    run_textract_pipeline("samples/sample_immigration_proposal.pdf")  # <- change path to test file
