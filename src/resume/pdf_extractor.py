import pymupdf


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text from an uploaded PDF file.

    Args:
        pdf_file: Streamlit UploadedFile or file-like object.

    Returns:
        Extracted text from all PDF pages.
    """

    pdf_bytes = pdf_file.read()

    document = pymupdf.open(stream=pdf_bytes, filetype="pdf")

    extracted_text = []

    for page in document:
        text = page.get_text()
        if text:
            extracted_text.append(text)

    document.close()

    return "\n".join(extracted_text).strip()