import pytest
import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import logging
from textract_utils import extract_text_from_bytes, is_likely_proposal

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load credentials
load_dotenv()

@pytest.fixture
def aws_textract():
    """Fixture to provide AWS Textract client"""
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        pytest.skip("AWS credentials not found")
    
    return boto3.client(
        'textract',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name="us-east-1"
    )

@pytest.fixture
def sample_image_bytes():
    """Fixture to provide sample image bytes"""
    image_path = os.path.join("backend", "assets", "demo.png")
    if not os.path.exists(image_path):
        pytest.skip(f"Sample image not found at {image_path}")
    with open(image_path, "rb") as f:
        return f.read()

def test_extract_text_from_bytes(aws_textract, sample_image_bytes):
    """Test text extraction from image bytes"""
    logger.debug("Testing text extraction")
    text = extract_text_from_bytes(sample_image_bytes)
    assert isinstance(text, str)
    assert len(text) > 0
    logger.debug(f"Extracted text length: {len(text)}")

def test_is_likely_proposal():
    """Test proposal detection logic"""
    # Test positive case
    text = "This is a legal proposal for USCIS form I-485 with attorney fees"
    assert is_likely_proposal(text) == True
    
    # Test negative case
    text = "This is a regular document without relevant keywords"
    assert is_likely_proposal(text) == False

def test_aws_credentials():
    """Test AWS credentials are properly loaded"""
    assert os.getenv("AWS_ACCESS_KEY_ID") is not None, "AWS access key not found"
    assert os.getenv("AWS_SECRET_ACCESS_KEY") is not None, "AWS secret key not found"
