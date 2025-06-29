import PyPDF2

def extract_text_by_page(pdf_path, page_num):
    print(f"Attempting to open PDF: {pdf_path}")
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"PDF opened successfully. Total pages: {len(pdf_reader.pages)}")
        if page_num < 1 or page_num > len(pdf_reader.pages):
            return "Page number out of range."
        page = pdf_reader.pages[page_num - 1]  # Pages are 0-indexed
        print(f"Extracting text from page {page_num}...")
        text = page.extract_text()
        print(f"Text extracted successfully. Length: {len(text)} characters")
        return text

# Example Usage:
print("Starting test.py execution...")
pdf_path = "2024Uworld MBE题库.pdf"
page_number = 1  # Extract text from page 1
print(f"Will extract text from {pdf_path}, page {page_number}")

try:
    text = extract_text_by_page(pdf_path, page_number)
    print(f"Page {page_number}:\n{text}...")  # Show first 500 characters
except Exception as e:
    print(f"Error occurred: {e}")
