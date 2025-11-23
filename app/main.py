from fastapi import FastAPI, File, UploadFile

from app.models import ParseResponse
from app.field_extractors.textract_field_extractor import TextractFieldExtractor
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return ParseResponse(success=False, error=str(exc)).__dict__


@app.get("/")
def root():
    return {"message": "1040 Parser API"}


@app.post("/parse-1040")
async def parse_1040(file: UploadFile = File(...)):
    """Parse a 1040 form using AWS Textract
    
    Args:
        file: PDF file uploaded via multipart/form-data
    """
    # Validate file type (optional but recommended)
    if file.filename and not file.filename.lower().endswith('.pdf'):
        return ParseResponse(success=False, error="Only PDF files are supported")
    
    # Read the file bytes
    try:
        doc_bytes = await file.read()
    except Exception as e:
        return ParseResponse(success=False, error=f"Error reading file: {str(e)}")

    fields_extractor = TextractFieldExtractor()
    try:
        blocks = fields_extractor.extract_pdf_blocks(doc_bytes)
        fields = await fields_extractor.extract_1040_fields(blocks)
    except Exception as e:
        return ParseResponse(success=False, error=f"Extract error: {str(e)}")
    if fields is None:
        return ParseResponse(success=False, error="Could not parse all required fields")
    return ParseResponse(success=True, fields=fields)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

