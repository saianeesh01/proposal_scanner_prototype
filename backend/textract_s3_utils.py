import boto3
import time
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = "us-east-1"
BUCKET_NAME = "immigration-proposals-scanner"  # TODO: Replace with your S3 bucket name

s3 = boto3.client('s3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION)

textract = boto3.client('textract',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION)

def upload_to_s3(file_bytes, filename):
    key = f"uploads/{uuid.uuid4()}_{filename}"
    s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=file_bytes)
    return key

def start_text_detection(s3_key):
    response = textract.start_document_text_detection(
        DocumentLocation={'S3Object': {'Bucket': BUCKET_NAME, 'Name': s3_key}}
    )
    return response['JobId']

def get_job_result(job_id):
    while True:
        response = textract.get_document_text_detection(JobId=job_id)
        status = response['JobStatus']
        if status in ['SUCCEEDED', 'FAILED']:
            break
        time.sleep(2)

    if status == 'SUCCEEDED':
        pages = []
        next_token = None
        while True:
            kwargs = {'JobId': job_id}
            if next_token:
                kwargs['NextToken'] = next_token
            result = textract.get_document_text_detection(**kwargs)
            pages.extend(result['Blocks'])
            next_token = result.get('NextToken')
            if not next_token:
                break
        return pages
    else:
        return []

# Optional: Add analyze_if_needed() next
def get_text(block, block_map):
    text = ""
    if 'Relationships' in block:
        for rel in block['Relationships']:
            if rel['Type'] == 'CHILD':
                for cid in rel['Ids']:
                    word = block_map.get(cid)
                    if word and word['BlockType'] == 'WORD':
                        text += word['Text'] + " "
    return text.strip()

def analyze_if_needed(s3_key):
    # Textract's analyze_document only works for:
    # - PNG, JPG, JPEG
    # - Single-page PDFs <10MB
    if not s3_key.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
        print("❌ Unsupported file format for AnalyzeDocument.")
        return []

    if s3_key.lower().endswith(".pdf"):
        print("⚠️ Skipping AnalyzeDocument: multi-page PDF likely unsupported for AnalyzeDocument.")
        return []

    try:
        response = textract.analyze_document(
            Document={'S3Object': {'Bucket': BUCKET_NAME, 'Name': s3_key}},
            FeatureTypes=['FORMS', 'TABLES']
        )

        blocks = response['Blocks']
        block_map = {b['Id']: b for b in blocks}
        key_values = []

        for block in blocks:
            if block['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
                key_text = get_text(block, block_map)

                value_block = None
                for rel in block.get('Relationships', []):
                    if rel['Type'] == 'VALUE':
                        for vid in rel['Ids']:
                            value_block = block_map.get(vid)

                value_text = get_text(value_block, block_map) if value_block else ""
                key_values.append((key_text, value_text))

        return key_values

    except textract.exceptions.UnsupportedDocumentException:
        print("❌ AnalyzeDocument failed: unsupported format.")
        return []

    except Exception as e:
        print(f"❌ Unexpected error in analyze_if_needed: {e}")
        return []

def is_structured_page(lines):
    """
    Heuristic to detect form-like structure.
    Flags pages that contain colons, key-value cues, or tabular content.
    """
    colon_count = sum(1 for line in lines if ':' in line)
    keyword_hits = sum(
        1 for line in lines
        if any(kw in line.lower() for kw in ["form", "date", "signature", "fee", "client", "table", "services"])
    )
    return colon_count >= 3 or keyword_hits >= 2
