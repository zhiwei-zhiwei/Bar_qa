import streamlit as st
import PyPDF2
import os
import re
import glob
from pathlib import Path

class StudyApp:
    def __init__(self):
        self.questions_dir = "all_questions"
        self.pdf_files = self.get_pdf_files()
        
    def get_pdf_files(self):
        """Get all PDF files in the questions directory, sorted numerically"""
        if not os.path.exists(self.questions_dir):
            return []
        
        pdf_files = glob.glob(os.path.join(self.questions_dir, "question_*.pdf"))
        # Sort numerically by question number
        pdf_files.sort(key=lambda x: int(re.search(r'question_(\d+)\.pdf', x).group(1)))
        return pdf_files
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file with improved formatting"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                # Apply comprehensive text cleaning
                text = self.clean_extracted_text(text)
                return text
        except Exception as e:
            st.error(f"Error reading PDF {pdf_path}: {str(e)}")
            return None
    
    def parse_question_and_explanation(self, text):
        """Parse the question and explanation from the text"""
        if not text:
            return None, None
        
        # Split by "Explanation:" to separate question from explanation
        parts = text.split("Explanation:")
        question_part = parts[0].strip()
        explanation_part = parts[1].strip() if len(parts) > 1 else "No explanation available."
        
        return question_part, explanation_part
    
    def extract_choices(self, question_text):
        """Extract multiple choice options from question text"""
        choices = {}
        
        # Clean up the text first
        cleaned_text = re.sub(r'\s+', ' ', question_text)
        
        # Try different approaches to find choices
        
        # Method 1: Look for A. B. C. D. patterns with flexible spacing
        pattern1 = r'([A-D])\.\s*([^A-D]*?)(?=\s*[A-D]\.\s*|$)'
        matches1 = re.findall(pattern1, cleaned_text, re.DOTALL)
        
        if len(matches1) >= 3:  # At least 3 choices found
            for letter, text in matches1:
                if letter in "ABCD" and text.strip():
                    choices[letter] = text.strip()
        
        # Method 2: Line-by-line with better handling
        if len(choices) < 3:
            choices = {}
            lines = question_text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Look for choice patterns
                for letter in ['A', 'B', 'C', 'D']:
                    pattern = rf'^{letter}\.\s*(.*)'
                    match = re.match(pattern, line)
                    if match:
                        choice_text = match.group(1).strip()
                        
                        # Look ahead for continuation lines
                        j = i + 1
                        while j < len(lines) and lines[j].strip() and not re.match(r'^[A-D]\.', lines[j].strip()):
                            choice_text += " " + lines[j].strip()
                            j += 1
                        
                        if choice_text:
                            choices[letter] = choice_text
                        break
        
        # Method 3: Handle cases where choices might be embedded differently
        if len(choices) < 3:
            choices = {}
            # Look for patterns like "A.text B.text C.text D.text"
            for letter in ['A', 'B', 'C', 'D']:
                pattern = rf'{letter}\.\s*([^{letter}]*?)(?=[A-D]\.|$)'
                match = re.search(pattern, cleaned_text, re.DOTALL)
                if match:
                    text = match.group(1).strip()
                    # Clean up the text
                    text = re.sub(r'[A-D]\..*$', '', text).strip()
                    if text and len(text) > 3:  # Must have some meaningful content
                        choices[letter] = text
        
        # Final cleanup of choices
        for letter in list(choices.keys()):
            if choices[letter]:
                # Remove any trailing choice letters that got included
                choices[letter] = re.sub(r'\s*[A-D]\.\s*$', '', choices[letter]).strip()
                # Remove if too short (likely parsing error)
                if len(choices[letter]) < 3:
                    del choices[letter]
        
        return choices
    
    def clean_question_text(self, question_text, choices):
        """Remove choice options from question text to get clean question"""
        # First apply general text cleaning
        clean_text = self.clean_extracted_text(question_text)
        
        # Split text into lines
        lines = clean_text.split('\n')
        question_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip lines that start with choice patterns (A., B., C., D.)
            if not re.match(r'^[A-D]\.\s', line):
                question_lines.append(line)
        
        # Join the remaining lines and clean up
        clean_text = '\n'.join(question_lines)
        
        # Additional cleanup: remove any remaining choice text that might be embedded
        for letter in ['A', 'B', 'C', 'D']:
            if letter in choices and choices[letter]:
                # Try to remove the choice text if it appears anywhere
                choice_text = choices[letter]
                if choice_text in clean_text:
                    clean_text = clean_text.replace(choice_text, "")
        
        # Remove any remaining choice patterns that might be embedded
        clean_text = re.sub(r'\b[A-D]\.\s*[^.]*?\s*(?=[A-D]\.|$)', '', clean_text)
        
        # Clean up extra whitespace and formatting
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)  # Multiple newlines to double newline
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)  # More than 2 newlines to double newline
        clean_text = re.sub(r'\s+', ' ', clean_text)  # Multiple spaces to single space
        clean_text = clean_text.strip()
        
        return clean_text

    def clean_extracted_text(self, text):
        """Clean and format text extracted from PDF to handle common issues"""
        if not text:
            return text
            
        # Fix concatenated words (lowercase followed by uppercase)
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # Fix sentences that got concatenated (period followed by capital letter)
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        # Fix number/letter combinations that got concatenated
        text = re.sub(r'(\d)([A-Z][a-z])', r'\1 \2', text)
        
        # Add proper spacing around common legal terms that might get concatenated
        text = re.sub(r'([a-z])(The|State|Court|Federal)', r'\1 \2', text)
        
        # Fix dollar amounts that might get concatenated
        text = re.sub(r'(\d),(\d{3})([A-Z])', r'\1,\2 \3', text)
        
        # Fix specific legal text patterns that often get garbled
        text = re.sub(r'([a-z])(State[A-Z])', r'\1 \2', text)
        text = re.sub(r'([a-z])(federal)', r'\1 \2', text)
        text = re.sub(r'(\d+)(days)', r'\1 \2', text)
        text = re.sub(r'([a-z])(after)', r'\1 \2', text)
        text = re.sub(r'([a-z])(being)', r'\1 \2', text)
        text = re.sub(r'([a-z])(served)', r'\1 \2', text)
        text = re.sub(r'([a-z])(with)', r'\1 \2', text)
        text = re.sub(r'([a-z])(process)', r'\1 \2', text)
        
        # Fix very long concatenated strings by adding spaces before capital letters
        # This handles cases like "ThecompanyfiledanoticeofremovalwiththefederalcourtinStateB14daysafterbeingservedwithprocess"
        text = re.sub(r'([a-z]{3,})([A-Z][a-z]{2,})', r'\1 \2', text)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Fix specific legal text patterns that often get garbled
        text = re.sub(r'([a-z])(State[A-Z])', r'\1 \2', text)
        text = re.sub(r'([a-z])(federal)', r'\1 \2', text)
        text = re.sub(r'(\d+)(days)', r'\1 \2', text)
        text = re.sub(r'([a-z])(after)', r'\1 \2', text)
        text = re.sub(r'([a-z])(being)', r'\1 \2', text)
        text = re.sub(r'([a-z])(served)', r'\1 \2', text)
        text = re.sub(r'([a-z])(with)', r'\1 \2', text)
        text = re.sub(r'([a-z])(process)', r'\1 \2', text)
        
        # Fix very long concatenated strings by adding spaces before capital letters
        # This handles cases like "ThecompanyfiledanoticeofremovalwiththefederalcourtinStateB14daysafterbeingservedwithprocess"
        text = re.sub(r'([a-z]{3,})([A-Z][a-z]{2,})', r'\1 \2', text)
        
        # Fix line breaks in the middle of sentences
        text = re.sub(r'([a-z,])\n([a-z])', r'\1 \2', text)
        
        return text.strip()

def main():
    st.set_page_config(
        page_title="Law Study Tool",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📚 Law Study Tool - MBE Practice Questions")
    
    # Initialize the study app
    app = StudyApp()
    
    if not app.pdf_files:
        st.error("No PDF files found in the 'all_questions' directory.")
        return
    
    # Initialize session state variables
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'user_answer' not in st.session_state:
        st.session_state.user_answer = None
    if 'show_explanation' not in st.session_state:
        st.session_state.show_explanation = False
    
    # Sidebar for navigation
    st.sidebar.header("📋 Question Navigation")
    
    total_questions = len(app.pdf_files)
    st.sidebar.write(f"Total Questions: {total_questions}")
    
    # Question selector in sidebar
    question_options = [f"Question {i+1}" for i in range(total_questions)]
    selected_question = st.sidebar.selectbox(
        "Jump to Question:",
        question_options,
        index=st.session_state.current_question_index
    )
    
    # Update current question index based on selection
    new_index = question_options.index(selected_question)
    if new_index != st.session_state.current_question_index:
        st.session_state.current_question_index = new_index
        st.session_state.user_answer = None
        st.session_state.show_explanation = False
        st.rerun()
    
    # Get current question
    current_pdf = app.pdf_files[st.session_state.current_question_index]
    question_number = st.session_state.current_question_index + 1
    
    # Extract and parse the current question
    text = app.extract_text_from_pdf(current_pdf)
    if text is None:
        st.error("Failed to load the current question.")
        return
    
    question_text, explanation = app.parse_question_and_explanation(text)
    choices = app.extract_choices(question_text)
    clean_question = app.clean_question_text(question_text, choices)
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header(f"Question {question_number}")
        
        # Display the question
        if clean_question:
            st.write(clean_question)
        else:
            st.error("Could not parse the question text.")
            return
        
        # Display choices and get user selection
        if choices:
            st.subheader("Select your answer:")
            
            choice_options = []
            for letter in ['A', 'B', 'C', 'D']:
                if letter in choices and choices[letter]:
                    choice_options.append(f"{letter}. {choices[letter]}")
            
            if choice_options:
                selected_choice = st.radio(
                    "Choose one:",
                    choice_options,
                    key=f"question_{question_number}_choice"
                )
                
                if selected_choice:
                    st.session_state.user_answer = selected_choice[0]  # Extract letter (A, B, C, or D)
            else:
                st.error("Could not extract answer choices from this question. Please check the PDF format.")
                # Debug information
                with st.expander("Debug Info (Click to expand)"):
                    st.write("Raw question text:")
                    st.text(question_text)
                    st.write("Extracted choices:")
                    st.write(choices)
        else:
            st.error("No answer choices found in this question.")
            # Debug information
            with st.expander("Debug Info (Click to expand)"):
                st.write("Raw question text:")
                st.text(question_text)
        
        # Show explanation after user selects an answer
        if st.session_state.user_answer:
            if st.button("Show Explanation", key="show_explanation_btn"):
                st.session_state.show_explanation = True
            
            if st.session_state.show_explanation:
                st.success(f"You selected: {st.session_state.user_answer}")
                st.subheader("📝 Explanation:")
                st.write(explanation)
    
    with col2:
        st.subheader("Navigation")
        
        # Previous button
        if st.button("⬅️ Previous Question", disabled=(st.session_state.current_question_index == 0)):
            st.session_state.current_question_index -= 1
            st.session_state.user_answer = None
            st.session_state.show_explanation = False
            st.rerun()
        
        # Next button
        if st.button("➡️ Next Question", disabled=(st.session_state.current_question_index == total_questions - 1)):
            st.session_state.current_question_index += 1
            st.session_state.user_answer = None
            st.session_state.show_explanation = False
            st.rerun()
        
        st.write("---")
        
        # View original PDF button
        if st.button("📄 View Original PDF"):
            pdf_name = os.path.basename(current_pdf)
            
            # Create a download button for the PDF
            try:
                with open(current_pdf, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                    st.download_button(
                        label=f"Download {pdf_name}",
                        data=pdf_bytes,
                        file_name=pdf_name,
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"Error loading PDF: {str(e)}")
        
        # Progress indicator
        st.write("---")
        st.subheader("Progress")
        progress = (st.session_state.current_question_index + 1) / total_questions
        st.progress(progress)
        st.write(f"{st.session_state.current_question_index + 1} of {total_questions}")
    
    # Footer
    st.write("---")
    st.info("💡 **How to use:** Read the question, select your answer, then click 'Show Explanation' to see the detailed explanation. Use the navigation buttons or sidebar to move between questions.")

if __name__ == "__main__":
    main() 