import boto3
import os
from dotenv import load_dotenv
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
logger.debug("Loading environment variables")
load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "us-east-1"

if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
    logger.warning("AWS credentials not found in environment variables")

try:
    logger.debug("Initializing AWS Textract client")
    textract = boto3.client(
        'textract',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )
except Exception as e:
    logger.error(f"Failed to initialize Textract client: {str(e)}")
    raise

def extract_text_from_bytes(file_bytes):
    """
    Extract text from document bytes using AWS Textract
    Args:
        file_bytes (bytes): Document bytes to process
    Returns:
        str: Extracted text from the document
    """
    logger.debug(f"Processing document of size: {len(file_bytes)} bytes")
    try:
        response = textract.detect_document_text(Document={'Bytes': file_bytes})
        lines = [block['Text'] for block in response['Blocks'] if block['BlockType'] == 'LINE']
        text = "\n".join(lines)
        logger.debug(f"Successfully extracted {len(lines)} lines of text")
        return text
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        logger.error(f"AWS Textract error: {error_code} - {error_msg}")
        raise
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise

def is_likely_proposal(text):
    """
    Check if the given text is likely to be a legal proposal
    Args:
        text (str): Text to analyze
    Returns:
        bool: True if the text is likely a proposal, False otherwise
    """
    keywords = [
        "scope of services", "legal fees", "uscis", "attorney",
        "asylum", "green card", "proposal", "i-130", "i-485", 
        "immigration", "client", "adjustment of status", 
        "form n-400", "daca", "naturalization"
    ]

    text_lower = text.lower()
    hit_count = sum(1 for word in keywords if word in text_lower)
    logger.debug(f"Found {hit_count} keyword matches in text")

    # Customize threshold if needed
    is_proposal = hit_count >= 3
    logger.debug(f"Document classified as proposal: {is_proposal}")
    return is_proposal
