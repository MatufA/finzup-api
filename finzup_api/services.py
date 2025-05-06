import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
from .config import get_settings
from .models import InvoiceData, Supplier, Recipient, InvoiceItem, Address
import json
import os
import fitz  # PyMuPDF for PDF processing
from PIL import Image
import io
import base64

settings = get_settings()
genai.configure(api_key=settings.GOOGLE_API_KEY)

# Initialize the Gemini model
model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.1,
)

model.with_structured_output(InvoiceData)

INVOICE_PROMPT = """
You are an expert at extracting structured data from invoices. 
Given an invoice image or PDF, Please analyze the document and extract the data.

If you cannot find certain fields, use null values.
The invoice should be in Hebrew, but can be in English. 
Keep the original invoice values, don't change them, don't translate them.
"""

def get_num_pages(file_content: bytes, file_type: str) -> int:
    if file_type == "pdf":
        doc = fitz.open(stream=file_content, filetype="pdf")
        return len(doc)
    return 1

def prepare_image_data(file_content: bytes, file_type: str) -> dict:
    if file_type == "pdf":
        doc = fitz.open(stream=file_content, filetype="pdf")
        image = doc[0].get_pixmap()
        image_bytes = image.tobytes()
        mime_type = "application/pdf"
    else:
        image = Image.open(io.BytesIO(file_content))
        image_bytes = file_content
        mime_type = f"image/{file_type}"

    # Convert to base64
    base64_data = base64.b64encode(image_bytes).decode('utf-8')
    
    return {
        "type": "image",
        "source_type": "base64",
        "data": base64_data,
        "mime_type": mime_type
    }

async def process_invoice(
    file_content: bytes,
    file_type: str,
    file_name: str,
    file_size: int
) -> Tuple[Optional[InvoiceData], Optional[str], int]:
    try:
        # Get number of pages
        num_pages = get_num_pages(file_content, file_type)
        
        # Prepare the image data
        image_data = prepare_image_data(file_content, file_type)

        # Create the message with multimodal content
        message = HumanMessage(
            content=[
                {
                    "type": "text", 
                    "text": INVOICE_PROMPT.format(
                        format_instructions=output_parser.get_format_instructions()
                    )
                },
                image_data
            ]
        )

        # Process with Gemini
        response = await model.ainvoke([message])

        # Parse the response
        try:
            # Parse the structured output directly into InvoiceData
            invoice_data = output_parser.parse(response.content)
            return invoice_data, None, len(response.content.split())
        except Exception as e:
            return None, f"Failed to parse invoice data: {str(e)}", 0

    except Exception as e:
        return None, str(e), 0 