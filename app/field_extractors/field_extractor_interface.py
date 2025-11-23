from abc import ABC, abstractmethod
from app.models import Form1040Fields


class FieldExtractorInterface(ABC):
    @abstractmethod
    def extract_pdf_blocks(self, document_bytes) -> dict:
        pass

    @abstractmethod
    def extract_1040_fields(self, blocks: dict) -> Form1040Fields | None:
        pass

