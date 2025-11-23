import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pathlib import Path
from io import BytesIO

from app.main import app

client = TestClient(app)


def load_fixture(filename):
    """Load a test fixture from the fixtures directory"""
    fixture_path = Path(__file__).parent / "fixtures" / filename
    with open(fixture_path, 'r') as f:
        return json.load(f)


class TestParse1040:
    """End-to-end tests for the 1040 parser"""
    
    @patch('app.field_extractors.textract_field_extractor.boto3.client')
    def test_parse_valid_1040(self, mock_boto_client):
        """Test parsing a valid 1040 with correct math"""
        # Setup mock
        mock_textract = MagicMock()
        mock_boto_client.return_value = mock_textract
        mock_textract.analyze_document.return_value = load_fixture('2024_samuel_singletary.json')
        
        # Create a fake PDF file for upload
        dummy_doc = b"fake pdf content"
        file_data = BytesIO(dummy_doc)
        
        # Make request with file upload
        response = client.post(
            "/parse-1040",
            files={"file": ("test_1040.pdf", file_data, "application/pdf")}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['fields'] is not None
        
        # Check parsed values from real Textract response
        fields = data['fields']
        assert fields['line_9'] == 280300.0
        assert fields['line_10'] == 9631.0
        assert fields['line_11'] == 270669.0
        
        # Check validation: line 11 should equal line 9 - line 10
        assert fields['is_valid'] is True
        
        # Verify Textract was called
        mock_textract.analyze_document.assert_called_once()
        call_args = mock_textract.analyze_document.call_args
        assert call_args[1]['FeatureTypes'] == ['FORMS']
    
    @patch('app.field_extractors.textract_field_extractor.boto3.client')
    def test_parse_invalid_1040_math(self, mock_boto_client):
        """Test parsing a 1040 where the math doesn't add up"""
        # Setup mock with invalid totals
        mock_textract = MagicMock()
        mock_boto_client.return_value = mock_textract
        mock_textract.analyze_document.return_value = load_fixture('sample_1040_invalid.json')
        
        # Create a fake PDF file for upload
        dummy_doc = b"fake pdf content"
        file_data = BytesIO(dummy_doc)
        
        # Make request with file upload
        response = client.post(
            "/parse-1040",
            files={"file": ("test_1040.pdf", file_data, "application/pdf")}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['fields'] is not None
        
        # Check that validation failed
        fields = data['fields']
        assert fields['is_valid'] is False
        
        # Line 11 should be 270669 (280300 - 9631) but is 260000 instead
        assert fields['line_9'] == 280300.0
        assert fields['line_10'] == 9631.0
        assert fields['line_11'] == 260000.0
    
    def test_root_endpoint(self):
        """Test the root endpoint returns expected message"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "1040 Parser API"}
    
    def test_invalid_file_type(self):
        """Test handling of non-PDF file uploads"""
        # Upload a non-PDF file
        dummy_doc = b"fake text content"
        file_data = BytesIO(dummy_doc)
        
        response = client.post(
            "/parse-1040",
            files={"file": ("test_document.txt", file_data, "text/plain")}
        )
        
        # Should get an error response
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False
        assert 'error' in data
        assert 'PDF' in data['error'] or 'pdf' in data['error']

