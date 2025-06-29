#!/usr/bin/env python3

import PyPDF2
import os
import re
from PyPDF2 import PdfReader, PdfWriter

def has_multiple_choice_options(text):
    """
    Check if the text contains all four multiple choice options: A., B., C., D.
    """
    # Look for patterns like "A.", "B.", "C.", "D." in the text
    pattern_a = r'\bA\.\s'
    pattern_b = r'\bB\.\s'
    pattern_c = r'\bC\.\s'
    pattern_d = r'\bD\.\s'
    
    has_a = bool(re.search(pattern_a, text))
    has_b = bool(re.search(pattern_b, text))
    has_c = bool(re.search(pattern_c, text))
    has_d = bool(re.search(pattern_d, text))
    
    return has_a and has_b and has_c and has_d

def split_pdf_by_questions(input_file, output_folder):
    """
    Split the PDF file into individual questions based on multiple choice options.
    """
    print(f"Reading PDF file: {input_file}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Read the PDF
    reader = PdfReader(input_file)
    total_pages = len(reader.pages)
    
    print(f"Total pages in PDF: {total_pages}")
    
    # Find question start pages
    question_starts = []
    
    for page_num in range(total_pages):
        try:
            page = reader.pages[page_num]
            text = page.extract_text()
            
            if has_multiple_choice_options(text):
                question_starts.append(page_num)
                print(f"Found question start at page {page_num + 1}")
        except Exception as e:
            print(f"Error processing page {page_num + 1}: {e}")
            continue
    
    print(f"Found {len(question_starts)} questions")
    
    # Split into individual PDFs
    for i, start_page in enumerate(question_starts):
        # Determine end page (start of next question or end of document)
        if i + 1 < len(question_starts):
            end_page = question_starts[i + 1] - 1
        else:
            end_page = total_pages - 1
        
        # Create a new PDF writer for this question
        writer = PdfWriter()
        
        # Add pages for this question
        for page_num in range(start_page, end_page + 1):
            try:
                writer.add_page(reader.pages[page_num])
            except Exception as e:
                print(f"Error adding page {page_num + 1} to question {i + 1}: {e}")
                continue
        
        # Write the question PDF
        output_filename = f"question_{i + 1}.pdf"
        output_path = os.path.join(output_folder, output_filename)
        
        try:
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            print(f"Created {output_filename} (pages {start_page + 1}-{end_page + 1})")
        except Exception as e:
            print(f"Error writing {output_filename}: {e}")
            continue
    
    print(f"Successfully split PDF into {len(question_starts)} question files")

if __name__ == "__main__":
    input_pdf = "2024Uworld MBE题库.pdf"
    output_directory = "all_questions"
    
    if not os.path.exists(input_pdf):
        print(f"Error: Input file '{input_pdf}' not found")
        exit(1)
    
    split_pdf_by_questions(input_pdf, output_directory) 