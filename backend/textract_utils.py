import boto3
import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "us-east-1"

textract = boto3.client(
    'textract',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def extract_text_from_bytes(file_bytes):
    response = textract.detect_document_text(Document={'Bytes': file_bytes})
    lines = [block['Text'] for block in response['Blocks'] if block['BlockType'] == 'LINE']
    return "\n".join(lines)


def is_likely_proposal(text):
    keywords = [
        "scope of services", "legal fees", "uscis", "attorney",
        "asylum", "green card", "proposal", "i-130", "i-485", 
        "immigration", "client", "adjustment of status", 
        "form n-400", "daca", "naturalization"
    ]

    text_lower = text.lower()
    hit_count = sum(1 for word in keywords if word in text_lower)

    # Customize threshold if needed
    return hit_count >= 3
