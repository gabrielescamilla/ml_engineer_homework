import base64
import os
import re
import json

from openai import OpenAI

from app.field_extractors.field_extractor import FieldExtractor
from app.models import Form1040Fields


class GPTExtractor(FieldExtractor):

    def extract_pdf_blocks(self, document_bytes) -> dict:
        """Call ChatGPT to analyze a 1040 form"""
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        processed_bytes = self.process_pdf_bytes(document_bytes)
        bytes_b64 =  base64.b64encode(processed_bytes).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{bytes_b64}"

        prompt = """
            Extract the following values from this 1040 tax document:
            - Total Income (Line 9)
            - Adjustments to Income (Line 10)
            - Adjusted Gross Income (Line 11)
            - Standard Deduction (Line 12)
            - Qualified Business Income Deduction (Line 13)
            - Total Deductions (Line 14)

            Format response as JSON:
            {
              "line_9": "numeric_value",
              "line_10": "numeric_value",
              "line_11": "numeric_value",
              "line_12": "numeric_value",
              "line_13": "numeric_value",
              "line_14": "numeric_value"
            }

            Use numbers only, no symbols. Return null for missing values.
            """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a tax expert that extracts financial data accurately "
                        "from documents."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type":"text",
                            "text": prompt
                        },
                        {
                            "type":"image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                },
            ]
        )
        content = response.choices[0].message.content
        clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
        return json.loads(clean)

    async def extract_1040_fields(self, fields: dict) -> Form1040Fields | None:

        float_fields = {
            "line_9": self._get_line_value(fields['line_9']),
            "line_10": self._get_line_value(fields['line_10']),
            "line_11": self._get_line_value(fields['line_11']),
            "line_12": self._get_line_value(fields['line_12']),
            "line_13": self._get_line_value(fields['line_13']),
            "line_14": self._get_line_value(fields['line_14'])
        }

        fields = Form1040Fields(**float_fields)
        return fields

    @staticmethod
    def _get_line_value(value_text: str | None) -> float | None:
        if value_text is None:
            return 0.0
        try:
            return float(value_text.replace(',', '').replace('$', '').replace('.', ''))
        except:
            pass
        return None


