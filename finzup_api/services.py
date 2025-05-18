from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.callbacks import get_usage_metadata_callback
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from typing import List, Optional, Tuple
from finzup_api.config import get_settings
from finzup_api.models import InvoiceData
from pydantic import BaseModel, Field
import fitz  # PyMuPDF for PDF processing
from PIL import Image
import io
import base64

settings = get_settings()

# Initialize the Gemini model
model = init_chat_model(model=settings.GEMINI_MODEL, model_provider="google_genai", temperature=0)

class ProcessInvoiceResponse(BaseModel):
    """Response model for invoice processing"""
    invoice_data: Optional[InvoiceData] = Field(None, description="The extracted invoice data")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    usage_metadata: dict = Field(default_factory=dict, description="Token usage metadata")

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

def prepare_image_data(file_content: bytes, file_type: str) -> str:
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
    
    # Return the base64 data with mime type
    return f"data:{mime_type};base64,{base64_data}"

async def process_invoice(
    file_content: bytes,
    file_type: str,
    file_name: str,
    file_size: int
) -> ProcessInvoiceResponse:
    try:
        # Get number of pages
        num_pages = get_num_pages(file_content, file_type)
        
        # Prepare the image data
        image_data = prepare_image_data(file_content, file_type)

        # Create the message with multimodal content
        message = HumanMessage(
            content=[
                INVOICE_PROMPT,
                {"type": "image_url", "image_url": image_data}
            ]
        )

        # Process with Gemini
        with get_usage_metadata_callback() as cb:
            response = await model.with_structured_output(InvoiceData).ainvoke([message])

            # Parse the response
            try:
                return ProcessInvoiceResponse(
                    invoice_data=response,
                    error=None,
                    usage_metadata=cb.usage_metadata
                )
            except Exception as e:
                return ProcessInvoiceResponse(
                    invoice_data=None,
                    error=f"Failed to parse invoice data: {str(e)}",
                    usage_metadata=cb.usage_metadata
                )

    except Exception as e:
        return ProcessInvoiceResponse(
            invoice_data=None,
            error=str(e),
            usage_metadata={}
        )
    
if __name__ == "__main__":
    import asyncio

    with open("/Users/adiel/git/invoce-scanner/data/invoices-images/invoice_14.jpeg", "rb") as f:
        file_content = f.read()
    result = asyncio.run(process_invoice(file_content, "jpeg", "test.jpeg", 1))
    print(f"Result: {result.model_dump_json(indent=2)}")