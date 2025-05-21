import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load credentials
load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "us-east-1"

# Initialize Textract client
textract = boto3.client(
    'textract',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def extract_text_from_document(document_path):
    try:
        with open(document_path, "rb") as document:
            image_bytes = document.read()

        response = textract.detect_document_text(Document={'Bytes': image_bytes})

        lines = []
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                lines.append(block['Text'])

        return lines

    except ClientError as e:
        print(f"Error occurred: {e}")
        return []

def main():
    # ✅ Use the working PDF path here
    document_path = "samples/sample_immigration_proposal.pdf"
    extracted_text = extract_text_from_document(document_path)

    print("\n--- Extracted Text ---\n")
    print("\n".join(extracted_text))

if __name__ == "__main__":
    main()
