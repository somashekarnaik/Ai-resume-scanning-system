try:
    import pymupdf as fitz  # pyright: ignore[reportMissingImports]
except ImportError:
    import fitz  # pyright: ignore[reportMissingImports]

def extract_pdf_text(
    file_path
):

    document = fitz.open(
        file_path
    )

    text = ""


    for page in document:

        text += page.get_text()


    document.close()


    return text