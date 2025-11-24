from abc import ABC, abstractmethod
from app.models import Form1040Fields
import io
from pdf2image import convert_from_bytes


class FieldExtractor(ABC):
    @abstractmethod
    def extract_pdf_blocks(self, document_bytes) -> dict:
        pass

    @abstractmethod
    def extract_1040_fields(self, blocks: dict) -> Form1040Fields | None:
        pass

    @staticmethod
    def process_pdf_bytes(document_bytes):
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
            except Exception as e:
                print(f"Error converting PDF to image: {str(e)}")
                pass
        return processed_bytes
