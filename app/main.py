from fastapi import FastAPI, File, UploadFile
from app.models import ParseResponse, Form1040Fields
from app.textract_helper import analyze_1040
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
    
    try:
        textract_response = analyze_1040(doc_bytes)
    except Exception as e:
        return ParseResponse(success=False, error=f"Textract error: {str(e)}")
    
    fields = {}
    blocks = textract_response.get('Blocks', [])
    
    # Look for key value pairs
    for block in blocks:
        if block['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
            # Get the key text
            key_text = ''
            if 'Relationships' in block:
                for relationship in block['Relationships']:
                    if relationship['Type'] == 'CHILD':
                        for child_id in relationship['Ids']:
                            for b in blocks:
                                if b['Id'] == child_id and b['BlockType'] == 'WORD':
                                    key_text += b.get('Text', '') + ' '
            
            key_text = key_text.strip().lower()
            
            # Find the corresponding value
            value_text = ''
            if 'Relationships' in block:
                for relationship in block['Relationships']:
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
            
            # Skip if no value
            if not value_text:
                continue
            
            # Line 9: Total income
            if (key_text.startswith('9 ') and 'total' in key_text and 'income' in key_text) or \
               ('9 add lines' in key_text):
                try:
                    fields['line_9'] = float(value_text.replace(',', '').replace('$', '').replace('.', ''))
                except:
                    pass
            # Line 10: Adjustments to income
            elif (key_text.startswith('10 ') and 'adjustment' in key_text) or \
                 (key_text.endswith(' 10') and 'adjustment' in key_text):
                try:
                    fields['line_10'] = float(value_text.replace(',', '').replace('$', '').replace('.', ''))
                except:
                    pass
            # Line 11: Adjusted gross income (AGI)
            elif (key_text.startswith('11 ') and 'subtract' in key_text) or \
                 (key_text.endswith(' 11') and 'adjusted gross income' in key_text):
                try:
                    fields['line_11'] = float(value_text.replace(',', '').replace('$', '').replace('.', ''))
                except:
                    pass
    
    # Check if we got all fields
    if len(fields) < 3:
        return ParseResponse(success=False, error="Could not parse all required fields")

    form_fields = Form1040Fields(
        line_9=fields['line_9'],
        line_10=fields['line_10'],
        line_11=fields['line_11']
    )
    
    return ParseResponse(success=True, fields=form_fields)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

