import streamlit as st
import pandas as pd
from PIL import Image
import io
import base64
import os
from pathlib import Path
import json
from typing import Union
import asyncio
from finzup_api.services import process_invoice, ProcessInvoiceResponse
from finzup_api.models import InvoiceData

def display_results(invoice_data: InvoiceData):
    # Display total amount
    st.write(f"Total Amount: {invoice_data.totalAmountNis} NIS")

    st.write(f"Invoice Number: {invoice_data.invoiceNumber}")
    st.write(f"Invoice Date: {invoice_data.invoiceDate}")

    # Display supplier information
    st.subheader("Supplier Information")
    st.write(f"Name: {invoice_data.supplier.name}")
    st.write(f"Address: {invoice_data.supplier.address.street}, {invoice_data.supplier.address.city}")
    if invoice_data.supplier.address.phone:
        st.write(f"Phone: {invoice_data.supplier.address.phone}")
    if invoice_data.supplier.address.email:
        st.write(f"Email: {invoice_data.supplier.address.email}")

    # Display recipient information
    st.subheader("Recipient Information")
    st.write(f"Name: {invoice_data.recipient.name}")
    st.write(f"Address: {invoice_data.recipient.address.street}, {invoice_data.recipient.address.city}")
    if invoice_data.recipient.address.phone:
        st.write(f"Phone: {invoice_data.recipient.address.phone}")
    if invoice_data.recipient.address.email:
        st.write(f"Email: {invoice_data.recipient.address.email}")

    # Display invoice items in a DataFrame
    st.subheader("Invoice Items")
    invoice_items = []
    for item in invoice_data.items:
        invoice_items.append({
            "Description": item.description,
            "Quantity": item.quantity,
            "Unit Price (NIS)": item.unitPriceNis,
            "Total Price (NIS)": item.totalPriceNis,
            "Barcode": item.barcode
        })
    
    df = pd.DataFrame(invoice_items)
    st.dataframe(df)

    # Calculate total from items
    calculated_total = sum(item.totalPriceNis for item in invoice_data.items)
    st.write(f"Calculated Total: {calculated_total} NIS")

    # Check if totals match or rounded match
    tax_price = 1.18
    if invoice_data.totalAmountNis:
        exact_match = -1 >= (calculated_total - invoice_data.totalAmountNis) <= 1
        tax_match = -1 >= (calculated_total * tax_price - invoice_data.totalAmountNis) <= 1

        if exact_match or tax_match:
            st.info("Invoice scanner are succeeded!")
        else:
            st.warning('Invoice scanner are failed, Total amount does not match calculated sum. Please verify manually.', icon="⚠️")


def main():
    st.set_page_config(page_title="Invoice Scanner", layout="wide")
    st.title("Invoice Scanner App")

    # Create two columns for side-by-side layout
    col1, col2 = st.columns(2)

    with col1:
        st.header("Upload Invoice")
        uploaded_file = st.file_uploader(
            "Choose an invoice file", 
            type=["pdf", "jpg", "jpeg", "png"]
        )

        if uploaded_file is not None:
            # Display preview
            if uploaded_file.type.startswith('image/'):
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_container_width=True)
            else:
                st.write("PDF file uploaded")

    with col2:
        st.header("Extracted Data")

        if uploaded_file is not None:
            st.write("File ready for processing")
            if st.button("Process Invoice"):
                with st.spinner("Processing invoice..."):
                    # Read file content
                    file_content = uploaded_file.getvalue()
                    file_type = uploaded_file.name.split('.')[-1].lower()
                    
                    # Process the invoice
                    result = asyncio.run(process_invoice(
                        file_content,
                        file_type,
                        uploaded_file.name,
                        len(file_content)
                    ))

                    if result.error:
                        st.error(f"Error processing invoice: {result.error}")
                    else:
                        st.success("Invoice processed successfully!")
                        display_results(result.invoice_data)
                        
                        # Save results to JSON
                        output_dir = Path('outputs')
                        output_dir.mkdir(exist_ok=True)
                        output_path = output_dir / f"{uploaded_file.name}.json"
                        
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(result.invoice_data.model_dump(), f, indent=4, ensure_ascii=False)
                        
                        st.info(f"Results saved to {output_path}")
                        
                        # Display token usage
                        st.subheader("Token Usage")
                        st.json(result.usage_metadata)
            else:
                st.write("Please upload an invoice file in the Upload section first.")

if __name__ == "__main__":
    main() 