from pydantic import BaseModel, model_validator
from typing import Optional


class Form1040Fields(BaseModel):
    """Parsed fields from Form 1040"""
    FLOAT_TOLERANCE: float = 0.01  # Allowed floating-point tolerance

    line_9: float   # Total income
    line_10: float  # Adjustments to income
    line_11: float  # Adjusted gross income (should be line 9 - line 10)
    is_valid: bool = False  # Whether the math checks out

    @model_validator(mode="after")
    def compute_is_valid(self) -> "Form1040Fields":
        calculated_line_11 = self.line_9 - self.line_10
        self.is_valid = abs(calculated_line_11 - self.line_11) < self.FLOAT_TOLERANCE
        return self



class ParseRequest(BaseModel):
    """Request to parse a 1040 document"""
    document_bytes: str  # Base64 encoded document
    

class ParseResponse(BaseModel):
    """Response containing parsed 1040 data"""
    success: bool
    fields: Optional[Form1040Fields] = None
    error: Optional[str] = None

