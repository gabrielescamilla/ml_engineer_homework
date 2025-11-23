from app.field_extractors.field_extractor_interface import FieldExtractorInterface
from app.models import Form1040Fields
import os
import boto3
import io
from pdf2image import convert_from_bytes


class TextractFieldExtractor(FieldExtractorInterface):
    def extract_pdf_blocks(self, document_bytes):
        """Call AWS Textract to analyze a 1040 form"""
        region = os.getenv("AWS_REGION", "us-east-1")

        client = boto3.client(
            "textract",
            region_name=region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        )

        # Try to detect if it's a PDF and convert to image
        processed_bytes = document_bytes
        if document_bytes.startswith(b'%PDF'):
            # Convert PDF first page to image
            try:
                images = convert_from_bytes(document_bytes, first_page=1, last_page=1)
                if images:
                    # Convert to JPEG bytes
                    img_byte_arr = io.BytesIO()
                    images[0].save(img_byte_arr, format='JPEG', quality=95)
                    processed_bytes = img_byte_arr.getvalue()
            except:
                pass

        response = client.analyze_document(
            Document={"Bytes": processed_bytes}, FeatureTypes=["FORMS"]
        )
        return response.get('Blocks', [])

    async def extract_1040_fields(self, blocks):
        fields = {}
        # Look for key value pairs
        for block in blocks:
            if block['BlockType'] != 'KEY_VALUE_SET' or 'KEY' not in block.get('EntityTypes', []) or 'Relationships' not in block:
                continue
            key_text = ''
            value_text = ''
            for relationship in block['Relationships']:
                # Get the key text
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        for b in blocks:
                            if b['Id'] == child_id and b['BlockType'] == 'WORD':
                                key_text += b.get('Text', '') + ' '

                    key_text = key_text.strip().lower()
                # Find the corresponding value
                if relationship['Type'] == 'VALUE':
                    for value_id in relationship['Ids']:
                        for value_block in blocks:
                            if value_block['Id'] == value_id:
                                if 'Relationships' in value_block:
                                    for vrel in value_block['Relationships']:
                                        if vrel['Type'] == 'CHILD':
                                            for vid in vrel['Ids']:
                                                for vb in blocks:
                                                    if vb['Id'] == vid and vb['BlockType'] == 'WORD':
                                                        value_text += vb.get('Text', '') + ' '

            value_text = value_text.strip()
            if not value_text:
                continue

            line_key = self._get_line_key(key_text)
            if line_key is None:
                continue
            line_value = self._get_line_value(value_text)
            if line_value is not None:
                fields[line_key] = line_value

        if len(fields) < 3:
            return None
        return Form1040Fields(
            line_9=fields['line_9'],
            line_10=fields['line_10'],
            line_11=fields['line_11']
        )

    def _get_line_key(self, key_text:str) -> str | None:
        # Line 9: Total income
        if (key_text.startswith('9 ') and 'total' in key_text and 'income' in key_text) or \
                ('9 add lines' in key_text):
            return 'line_9'
        # Line 10: Adjustments to income
        if (key_text.startswith('10 ') and 'adjustment' in key_text) or \
                (key_text.endswith(' 10') and 'adjustment' in key_text):
            return 'line_10'
        # Line 11: Adjusted gross income (AGI)
        if (key_text.startswith('11 ') and 'subtract' in key_text) or \
                (key_text.endswith(' 11') and 'adjusted gross income' in key_text):
            return 'line_11'
        return None

    def _get_line_value(self, value_text:str) -> float | None:
        try:
            return float(value_text.replace(',', '').replace('$', '').replace('.', ''))
        except:
            pass
        return None
