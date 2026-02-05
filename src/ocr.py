import fitz
import io
from markitdown import MarkItDown

def parse_pdf(pdf_path):
    markitdown = MarkItDown()
    doc = fitz.open(pdf_path)
    pdf_data = []

    for page_num in range(len(doc)):
        single_page_doc = fitz.open()
        single_page_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
        # 1. Get the raw bytes
        pdf_bytes = single_page_doc.tobytes()
        
        # 2. WRAP bytes in a Seekable Stream
        pdf_stream = io.BytesIO(pdf_bytes)
        
        # 3. Pass the stream instead of the raw bytes
        result = markitdown.convert_stream(pdf_stream, file_extension=".pdf")
        
        page_entry = {
            "page_number": page_num + 1,
            "content": result.text_content.strip(),
        }
        
        pdf_data.append(page_entry)
        single_page_doc.close()

    doc.close()

    return pdf_data