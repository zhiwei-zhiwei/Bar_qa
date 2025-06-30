import streamlit as st
import os
import re
import glob
from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import tempfile
import json
import base64

class StudyAppOCR:
    def __init__(self):
        self.questions_dir = "all_questions"
        self.pdf_files = self.get_pdf_files()
        self.answers_file = "correct_answers.json"
        self.load_or_create_answers_file()
        self.init_session_state()
        
    def init_session_state(self):
        """Initialize session state variables"""
        if 'current_question' not in st.session_state:
            st.session_state.current_question = 1
        if 'show_explanation' not in st.session_state:
            st.session_state.show_explanation = False
        if 'ocr_cache' not in st.session_state:
            st.session_state.ocr_cache = {}
        if 'question_data_cache' not in st.session_state:
            st.session_state.question_data_cache = {}
        if 'current_user' not in st.session_state:
            st.session_state.current_user = ""
        if 'user_answers_file' not in st.session_state:
            st.session_state.user_answers_file = ""
        
    def load_or_create_answers_file(self):
        """Load existing answers file or create a new one"""
        if os.path.exists(self.answers_file):
            try:
                with open(self.answers_file, 'r') as f:
                    self.answers_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.answers_data = {}
        else:
            self.answers_data = {}
            self.save_answers_file()
    
    def save_answers_file(self):
        """Save answers to JSON file"""
        try:
            with open(self.answers_file, 'w') as f:
                json.dump(self.answers_data, f, indent=2)
        except Exception as e:
            st.error(f"Error saving answers file: {str(e)}")
    
    def get_stored_correct_answer(self, question_number):
        """Get correct answer from JSON file if available"""
        question_key = f"Question_{question_number}"
        return self.answers_data.get(question_key, {}).get("Correct_result", None)
    
    def store_correct_answer(self, question_number, correct_answer):
        """Store correct answer in JSON file"""
        question_key = f"Question_{question_number}"
        if question_key not in self.answers_data:
            self.answers_data[question_key] = {}
        self.answers_data[question_key]["Correct_result"] = correct_answer
        self.save_answers_file()
    
    def store_user_choice(self, question_number, user_choice):
        """Store user's choice in JSON file"""
        question_key = f"Question_{question_number}"
        if question_key not in self.answers_data:
            self.answers_data[question_key] = {}
        self.answers_data[question_key]["Users_choice"] = user_choice
        self.save_answers_file()
    
    def get_user_choice(self, question_number):
        """Get user's choice from JSON file if available"""
        question_key = f"Question_{question_number}"
        return self.answers_data.get(question_key, {}).get("Users_choice", None)
    
    def get_question_status(self, question_number):
        """Get question status: 'correct', 'wrong', 'needs_answer'"""
        correct_answer = self.get_stored_correct_answer(question_number)
        user_choice = self.get_user_choice(question_number)
        
        if not correct_answer:
            return 'needs_answer'
        elif not user_choice:
            return 'needs_answer'
        elif correct_answer == user_choice:
            return 'correct'
        else:
            return 'wrong'
        
    def get_pdf_files(self):
        """Get all PDF files in the questions directory, sorted numerically"""
        if not os.path.exists(self.questions_dir):
            return []
        
        pdf_files = glob.glob(os.path.join(self.questions_dir, "question_*.pdf"))
        # Sort numerically by question number
        pdf_files.sort(key=lambda x: int(re.search(r'question_(\d+)\.pdf', x).group(1)))
        return pdf_files
    
    def extract_text_from_pdf_ocr(self, pdf_path):
        """Extract text from PDF using OCR"""
        try:
            # Check if poppler is available
            import subprocess
            try:
                subprocess.run(['pdftoppm', '-h'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                st.error("⚠️ OCR dependencies not available in deployment environment. Please install poppler-utils.")
                st.info("💡 This app requires system dependencies that may not be available in all deployment environments.")
                return None
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            all_text = ""
            for i, image in enumerate(images):
                # Extract text using OCR
                text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')
                all_text += text + "\n"
            
            return all_text
            
        except Exception as e:
            st.error(f"Error extracting text from {pdf_path}: {str(e)}")
            st.info("💡 If you're seeing this error in deployment, make sure poppler-utils is installed via packages.txt")
            return None
    
    def parse_question_and_explanation(self, text):
        """Parse the question and explanation from the OCR text"""
        if not text:
            return None, None
        
        # Clean up OCR artifacts
        text = self.clean_ocr_text(text)
        
        # Split by "Explanation:" to separate question from explanation
        parts = text.split("Explanation:")
        question_part = parts[0].strip()
        explanation_part = parts[1].strip() if len(parts) > 1 else "No explanation available."
        
        return question_part, explanation_part
    
    def clean_ocr_text(self, text):
        """Clean up common OCR artifacts and errors"""
        if not text:
            return text
        
        # Remove page markers
        text = re.sub(r'--- Page \d+ ---', '', text)
        
        # Fix common OCR errors
        text = re.sub(r'\|', 'I', text)  # Vertical bars often misread as I
        text = re.sub(r'0(?=[A-Za-z])', 'O', text)  # Zero misread as O before letters
        text = re.sub(r'(?<=[A-Za-z])0', 'o', text)  # Zero misread as o after letters
        text = re.sub(r'rn', 'm', text)  # Common OCR error
        text = re.sub(r'(?<=[a-z])1(?=[a-z])', 'l', text)  # 1 misread as l
        
        # Fix spacing issues
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Clean up line breaks
        
        # Fix sentence spacing
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        return text.strip()
    
    def extract_choices_ocr(self, question_text):
        """Extract multiple choice options from OCR text"""
        choices = {}
        
        # Clean the text first
        cleaned_text = self.clean_ocr_text(question_text)
        
        # Remove page markers if present
        cleaned_text = re.sub(r'--- Page \d+ ---[^\n]*\n?', '', cleaned_text)
        
        # Split into lines for processing
        lines = cleaned_text.split('\n')
        
        # Look for lines that start with A., B., C., D.
        current_choice = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with a choice pattern
            choice_match = re.match(r'^([A-D])\.\s*(.*)', line)
            if choice_match:
                # Save previous choice if exists
                if current_choice and current_text:
                    choice_content = ' '.join(current_text).strip()
                    if len(choice_content) > 3:
                        choices[current_choice] = choice_content
                
                # Start new choice
                current_choice = choice_match.group(1)
                current_text = [choice_match.group(2)] if choice_match.group(2) else []
            elif current_choice and line:
                # Check if this line starts a new choice
                if not re.match(r'^[A-D]\.', line):
                    # Continue current choice text (multi-line choice)
                    current_text.append(line)
                # If it does start with a choice, we'll handle it in the next iteration
        
        # Don't forget the last choice
        if current_choice and current_text:
            choice_content = ' '.join(current_text).strip()
            if len(choice_content) > 3:
                choices[current_choice] = choice_content
        
        # Final cleanup
        for letter in list(choices.keys()):
            if choices[letter]:
                # Remove any trailing patterns that might have been included
                choices[letter] = re.sub(r'\s*[A-D]\.\s*.*$', '', choices[letter]).strip()
                # Remove if too short
                if len(choices[letter]) < 3:
                    del choices[letter]
        
        return choices
    
    def extract_choices_from_raw_text(self, raw_text):
        """Extract choices directly from raw OCR text (same logic as debug info)"""
        choices = {}
        
        if not raw_text:
            return choices
        
        # Split by "Explanation:" to get only the question part
        question_only = raw_text.split("Explanation:")[0].strip()
        
        # Split into lines for processing
        lines = question_only.split('\n')
        
        # Look for lines that start with A., B., C., D.
        current_choice = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with a choice pattern
            choice_match = re.match(r'^([A-D])\.\s*(.*)', line)
            if choice_match:
                # Save previous choice if exists
                if current_choice and current_text:
                    choice_content = ' '.join(current_text).strip()
                    if len(choice_content) > 3:
                        choices[current_choice] = choice_content
                
                # Start new choice
                current_choice = choice_match.group(1)
                current_text = [choice_match.group(2)] if choice_match.group(2) else []
            elif current_choice and line:
                # Check if this line starts a new choice
                if not re.match(r'^[A-D]\.', line):
                    # Continue current choice text (multi-line choice)
                    current_text.append(line)
        
        # Don't forget the last choice
        if current_choice and current_text:
            choice_content = ' '.join(current_text).strip()
            if len(choice_content) > 3:
                choices[current_choice] = choice_content
        
        return choices
    
    def clean_question_text_ocr(self, question_text, choices):
        """Remove choice options from question text to get clean question"""
        clean_text = self.clean_ocr_text(question_text)
        
        # Remove page markers
        clean_text = re.sub(r'--- Page \d+ ---[^\n]*\n?', '', clean_text)
        
        # Split into lines and remove choice lines
        lines = clean_text.split('\n')
        question_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip lines that start with choice patterns (A., B., C., D.)
            if re.match(r'^[A-D]\.\s', line):
                break  # Stop processing once we hit the first choice
                
            question_lines.append(line)
        
        # Join the remaining lines
        clean_text = ' '.join(question_lines)
        
        # Additional cleanup
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = clean_text.strip()
        
        return clean_text
    
    def get_cached_question_data(self, pdf_path, question_number):
        """Get cached question data or extract it if not cached"""
        cache_key = f"question_{question_number}"
        
        # Check if this question is already cached
        if cache_key in st.session_state.question_data_cache:
            cached_data = st.session_state.question_data_cache[cache_key]
            return cached_data['raw_text'], cached_data['question_text'], cached_data['explanation'], cached_data['choices'], cached_data['final_question'], cached_data['correct_answer']
        
        # If not cached, extract the data with a progress indicator
        with st.spinner(f"Processing Question {question_number} with OCR..."):
            # Extract text using OCR
            raw_text = self.extract_text_from_pdf_ocr(pdf_path)
            if raw_text is None:
                return None, None, None, None, None, None
            
            # Parse the data
            question_text, explanation = self.parse_question_and_explanation(raw_text)
            choices = self.extract_choices_from_raw_text(raw_text)
            
            # Process question display text
            question_only = raw_text.split("Explanation:")[0].strip()
            lines = question_only.split('\n')
            question_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if re.match(r'^[A-D]\.\s', line):
                    break
                question_lines.append(line)
            
            final_question = ' '.join(question_lines)
            final_question = re.sub(r'\s+', ' ', final_question).strip()
            
            # Find the correct answer - first check stored answers, then auto-detect
            stored_answer = self.get_stored_correct_answer(question_number)
            if stored_answer:
                correct_answer = stored_answer
            else:
                correct_answer = self.find_correct_answer(explanation)
                # If we found an answer, store it
                if correct_answer:
                    self.store_correct_answer(question_number, correct_answer)
            
            # Cache the results
            cached_data = {
                'raw_text': raw_text,
                'question_text': question_text,
                'explanation': explanation,
                'choices': choices,
                'final_question': final_question,
                'correct_answer': correct_answer
            }
            
            st.session_state.question_data_cache[cache_key] = cached_data
            
        return cached_data['raw_text'], cached_data['question_text'], cached_data['explanation'], cached_data['choices'], cached_data['final_question'], cached_data['correct_answer']
    
    def find_correct_answer(self, explanation):
        """Find the correct answer by analyzing which choices are marked as wrong in the explanation"""
        if not explanation:
            return None
        
        # All possible choices
        all_choices = {'A', 'B', 'C', 'D'}
        wrong_choices = set()
        
        # Patterns to find wrong choices in explanation
        wrong_choice_patterns = [
            r'\(Choice ([A-D])\)',
            r'\(Choice ([A-D]) & ([A-D])\)',
            r'\(Choice ([A-D]) & ([A-D]) & ([A-D])\)',
            r'\(Choice ([A-D]), ([A-D]), & ([A-D])\)',
            r'\(Choice ([A-D]), ([A-D]), and ([A-D])\)',
            r'\(Choice ([A-D]) and ([A-D])\)',
        ]
        
        # Find all wrong choices mentioned in the explanation
        for pattern in wrong_choice_patterns:
            matches = re.findall(pattern, explanation, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Multiple choices in one match
                    for choice in match:
                        if choice and choice in all_choices:
                            wrong_choices.add(choice)
                else:
                    # Single choice
                    if match in all_choices:
                        wrong_choices.add(match)
        
        # The correct choice is the one NOT mentioned as wrong
        correct_choices = all_choices - wrong_choices
        
        # Should have exactly one correct choice
        if len(correct_choices) == 1:
            return list(correct_choices)[0]
        
        return None

    def get_user_answers_file(self, username):
        """Get the JSON file path for a specific user"""
        if not username:
            return None
        # Create safe filename from username
        safe_username = re.sub(r'[^\w\-_\.]', '_', username)
        return f"user_answers_{safe_username}.json"
    
    def load_user_answers(self, answers_file):
        """Load user answers from JSON file"""
        if not answers_file or not os.path.exists(answers_file):
            return {}
        try:
            with open(answers_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading user answers: {e}")
            return {}
    
    def save_user_answers(self, answers_file, answers_data):
        """Save user answers to JSON file"""
        if not answers_file:
            return
        try:
            with open(answers_file, 'w', encoding='utf-8') as f:
                json.dump(answers_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            st.error(f"Error saving user answers: {e}")

    def user_management_section(self):
        """Handle user login/creation section"""
        st.markdown("### 👤 User Management")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            username = st.text_input(
                "Enter your name to track your progress:",
                value=st.session_state.current_user,
                placeholder="Enter your name (e.g., John Doe)",
                help="Each user gets their own progress tracking file"
            )
        
        with col2:
            if st.button("Login/Create User", type="primary", use_container_width=True):
                if username.strip():
                    st.session_state.current_user = username.strip()
                    st.session_state.user_answers_file = self.get_user_answers_file(username.strip())
                    st.success(f"✅ Logged in as: {username.strip()}")
                    st.rerun()
                else:
                    st.error("Please enter a valid name")
        
        # Show current user status
        if st.session_state.current_user:
            st.info(f"📚 Currently studying as: **{st.session_state.current_user}**")
            
            # Show user's progress summary
            if st.session_state.user_answers_file:
                user_answers = self.load_user_answers(st.session_state.user_answers_file)
                total_questions = self.get_total_questions()
                answered_questions = len([q for q, data in user_answers.items() if data.get('Users_choice')])
                correct_answers = len([q for q, data in user_answers.items() 
                                     if data.get('Users_choice') == data.get('Correct_result')])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Questions Answered", f"{answered_questions}/{total_questions}")
                with col2:
                    st.metric("Correct Answers", correct_answers)
                with col3:
                    accuracy = round((correct_answers / answered_questions * 100), 1) if answered_questions > 0 else 0
                    st.metric("Accuracy", f"{accuracy}%")
        else:
            st.warning("⚠️ Please enter your name to start tracking your progress")
            return False
        
        return True

    def get_question_status_for_user(self, question_num, user_answers):
        """Get status for a specific question for the current user"""
        question_key = f"Question_{question_num}"
        if question_key not in user_answers:
            return "🤔"  # Needs answer
        
        question_data = user_answers[question_key]
        users_choice = question_data.get('Users_choice')
        correct_result = question_data.get('Correct_result')
        
        if not users_choice:
            return "🤔"  # Needs answer
        elif users_choice == correct_result:
            return "✅"  # Correct
        else:
            return "❌"  # Wrong

    def update_user_answer(self, question_num, user_choice, correct_answer=None):
        """Update user's answer in their personal JSON file"""
        if not st.session_state.user_answers_file:
            return
        
        user_answers = self.load_user_answers(st.session_state.user_answers_file)
        question_key = f"Question_{question_num}"
        
        if question_key not in user_answers:
            user_answers[question_key] = {}
        
        user_answers[question_key]["Users_choice"] = user_choice
        if correct_answer:
            user_answers[question_key]["Correct_result"] = correct_answer
        
        self.save_user_answers(st.session_state.user_answers_file, user_answers)

    def get_total_questions(self):
        """Get total number of questions available"""
        return len(self.pdf_files)

    def create_pdf_viewer_options(self, pdf_path, question_number):
        """Create multiple PDF viewing options for better compatibility"""
        pdf_name = os.path.basename(pdf_path)
        
        try:
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                
                st.markdown(f"**📄 File:** `{pdf_name}`")
                
                # Option 1: Download button (most reliable across all browsers)
                st.download_button(
                    label="💾 Download PDF",
                    data=pdf_bytes,
                    file_name=pdf_name,
                    mime="application/pdf",
                    key=f"download_pdf_{question_number}",
                    help="Most reliable option: Download and open in your PDF viewer",
                    use_container_width=True
                )
                
                st.markdown("---")
                st.markdown("**🔍 Quick Preview Options:**")
                
                # Option 2: PDF as Images (most compatible for viewing)
                if st.checkbox("🖼️ Show as Images", key=f"img_pdf_{question_number}", help="Convert PDF to images for viewing"):
                    try:
                        # Check if we have the conversion capability
                        images = convert_from_path(pdf_path, dpi=150)
                        
                        for i, image in enumerate(images):
                            st.image(image, caption=f"Page {i+1} of {pdf_name}", use_column_width=True)
                            
                    except Exception as e:
                        st.error(f"Could not convert PDF to images: {str(e)}")
                        st.info("💡 Please use the download button to view the PDF.")
                
                # Option 3: Embedded viewer (may not work in all environments)
                if st.checkbox("📖 Try Embedded Viewer", key=f"embed_pdf_{question_number}", help="May not work in all browsers/deployments"):
                    b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                    
                    # More robust iframe approach
                    st.markdown(f"""
                    <div style="width: 100%; height: 500px; border: 2px solid #ddd; border-radius: 10px; overflow: hidden; background-color: #f8f9fa;">
                        <object data="data:application/pdf;base64,{b64_pdf}" 
                                type="application/pdf" 
                                width="100%" 
                                height="100%">
                            <embed src="data:application/pdf;base64,{b64_pdf}" 
                                   type="application/pdf" 
                                   width="100%" 
                                   height="100%">
                                <div style="padding: 20px; text-align: center;">
                                    <p style="color: #666;">📄 PDF cannot be displayed in this browser.</p>
                                    <p style="color: #666;">Please use the download button above to view the PDF.</p>
                                </div>
                            </embed>
                        </object>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("💡 If nothing appears above, your browser doesn't support embedded PDFs. Use the download option instead.")
                
                # Option 4: Direct link (backup)
                if st.checkbox("🔗 Direct Link Method", key=f"link_pdf_{question_number}", help="Alternative link-based approach"):
                    b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                    pdf_data_url = f"data:application/pdf;base64,{b64_pdf}"
                    
                    st.markdown(f"""
                    <a href="{pdf_data_url}" target="_blank" 
                       style="display: inline-block; background-color: #007bff; color: white; 
                       padding: 12px 24px; text-decoration: none; border-radius: 8px; 
                       font-weight: bold; margin: 5px;">
                        🌐 Open in New Tab
                    </a>
                    """, unsafe_allow_html=True)
                    
                    st.warning("⚠️ This method may show 'about:blank' in some browsers or deployment environments.")
                
        except Exception as e:
            st.error(f"Error loading PDF: {str(e)}")
            st.info("The PDF file might be corrupted or inaccessible.")

def main():
    st.set_page_config(
        page_title="Law Study Tool (OCR)",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📚 Law Study Tool - MBE Practice Questions (OCR Version)")
    st.info("🔍 This version uses OCR (Optical Character Recognition) for better text extraction from PDFs")
    
    # Initialize the study app
    app = StudyAppOCR()
    
    if not app.pdf_files:
        st.error("No PDF files found in the 'all_questions' directory.")
        return
    
    # User Management Section (BEFORE Question Navigation)
    user_logged_in = app.user_management_section()
    if not user_logged_in:
        st.stop()  # Stop here if user not logged in
    
    st.markdown("---")
    
    # Initialize session state variables
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'user_answer' not in st.session_state:
        st.session_state.user_answer = None
    if 'show_explanation' not in st.session_state:
        st.session_state.show_explanation = False
    if 'ocr_cache' not in st.session_state:
        st.session_state.ocr_cache = {}
    if 'question_data_cache' not in st.session_state:
        st.session_state.question_data_cache = {}
    
    # Sidebar for navigation
    st.sidebar.header("📋 Question Navigation")
    
    # Load current user's answers
    user_answers = app.load_user_answers(st.session_state.user_answers_file)
    total_questions = len(app.pdf_files)
    st.sidebar.write(f"Total Questions: {total_questions}")
    
    # Show statistics for current user
    correct_count = 0
    wrong_count = 0
    needs_answer_count = 0
    
    for i in range(total_questions):
        status = app.get_question_status_for_user(i + 1, user_answers)
        if status == '✅':
            correct_count += 1
        elif status == '❌':
            wrong_count += 1
        else:
            needs_answer_count += 1
    
    st.sidebar.metric("✅ Correct", correct_count)
    st.sidebar.metric("❌ Wrong", wrong_count)
    st.sidebar.metric("🤔 Needs Answer", needs_answer_count)
    
    # Filter section for wrong answers
    if wrong_count > 0:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ❌ Review Wrong Answers")
        wrong_questions = []
        for i in range(total_questions):
            if app.get_question_status_for_user(i + 1, user_answers) == '❌':
                wrong_questions.append(f"Question {i + 1}")
        
        if wrong_questions:
            selected_wrong = st.sidebar.selectbox(
                "Jump to wrong answer:",
                [""] + wrong_questions,
                key="wrong_filter"
            )
            if selected_wrong:
                wrong_num = int(selected_wrong.split()[1]) - 1
                if wrong_num != st.session_state.current_question_index:
                    st.session_state.current_question_index = wrong_num
                    st.session_state.user_answer = None
                    st.session_state.show_explanation = False
                    st.rerun()
    
    # Show answer summary (expandable)
    if correct_count + wrong_count > 0:
        with st.sidebar.expander("📊 View All Results"):
            for question_key in sorted(user_answers.keys(), key=lambda x: int(x.split('_')[1])):
                q_num = question_key.split('_')[1]
                correct_answer = user_answers[question_key].get("Correct_result")
                user_choice = user_answers[question_key].get("Users_choice")
                if correct_answer and user_choice:
                    if correct_answer == user_choice:
                        st.success(f"Q{q_num}: {user_choice} ✓")
                    else:
                        st.error(f"Q{q_num}: {user_choice} (Correct: {correct_answer})")
    
    st.sidebar.markdown("---")
    
    # Question selector in sidebar with status indicators
    question_options = []
    for i in range(total_questions):
        question_num = i + 1
        status = app.get_question_status_for_user(question_num, user_answers)
        question_options.append(f"{status} Question {question_num}")
    selected_question = st.sidebar.selectbox(
        "Jump to Question:",
        question_options,
        index=st.session_state.current_question_index
    )
    
    # Update current question index based on selection
    # Extract question number from the selected option (e.g., "✅ Question 1" -> 0)
    selected_number = int(selected_question.split("Question ")[1]) - 1
    if selected_number != st.session_state.current_question_index:
        st.session_state.current_question_index = selected_number
        st.session_state.user_answer = None
        st.session_state.show_explanation = False
        st.rerun()
    
    # Get current question
    current_pdf = app.pdf_files[st.session_state.current_question_index]
    question_number = st.session_state.current_question_index + 1
    
    # Get cached question data (OCR runs only once per question)
    cached_result = app.get_cached_question_data(current_pdf, question_number)
    if cached_result[0] is None:  # raw_text is None
        st.error("Failed to load the current question.")
        return
    
    text, question_text, explanation, choices, final_question, correct_answer = cached_result
    
    # Progress section
    st.subheader("📊 Progress")
    progress = (st.session_state.current_question_index + 1) / total_questions
    st.progress(progress)
    st.write(f"Question {st.session_state.current_question_index + 1} of {total_questions}")
    
    st.markdown("---")
    
    # Main content area
    st.header(f"Question {question_number}")
    
    # Display the cached question (no OCR processing needed)
    if final_question:
        st.write(final_question)
    else:
        st.error("Could not parse the question text.")
        return
    
    # Display choices and get user selection
    if choices and len(choices) >= 2:  # At least 2 choices found
        st.subheader("Select your answer:")
        
        choice_options = []
        for letter in ['A', 'B', 'C', 'D']:
            if letter in choices and choices[letter]:
                choice_options.append(f"{letter}. {choices[letter]}")
        
        if choice_options:
            selected_choice = st.radio(
                "Choose one:",
                choice_options,
                index=None,  # No pre-selection
                key=f"question_{question_number}_choice"
            )
            
            if selected_choice:
                st.session_state.user_answer = selected_choice[0]  # Extract letter (A, B, C, or D)
        else:
            st.error("Could not extract answer choices from this question.")
            # Debug information
            with st.expander("Debug Info (Click to expand)"):
                st.write("Raw OCR text:")
                st.text(text)
                st.write("Question text:")
                st.text(question_text)
                st.write("Extracted choices:")
                st.write(choices)
    else:
        st.error("No answer choices found in this question.")
        # Debug information
        with st.expander("Debug Info (Click to expand)"):
            st.write("Raw OCR text:")
            st.text(text)
            st.write("Question text:")
            st.text(question_text)
            st.write("Extracted choices:")
            st.write(choices)
        
    # Submit and Show Explanation buttons (separate section)
    if st.session_state.user_answer:
        # Check if already submitted in user's personal file
        question_key = f"Question_{question_number}"
        already_submitted = user_answers.get(question_key, {}).get('Users_choice')
        
        st.markdown("---")  # Add separator
        st.subheader("📝 Submit & Review")
        
        action_col1, action_col2 = st.columns([1, 1])
        
        with action_col1:
            if already_submitted:
                submit_clicked = st.button("🔄 Update Answer", key="submit_answer_btn", type="secondary", use_container_width=True)
            else:
                submit_clicked = st.button("📝 Submit Answer", key="submit_answer_btn", type="primary", use_container_width=True)
            
            if submit_clicked:
                app.update_user_answer(question_number, st.session_state.user_answer, correct_answer)
                # Force sidebar refresh by updating session state
                if 'sidebar_refresh' not in st.session_state:
                    st.session_state.sidebar_refresh = 0
                st.session_state.sidebar_refresh += 1
                # Show success message and refresh
                if already_submitted:
                    st.success("✅ Answer updated!", icon="✅")
                else:
                    st.success("✅ Answer submitted!", icon="✅")
                st.rerun()
        
        with action_col2:
            if st.button("📖 Show Explanation", key="show_explanation_btn", use_container_width=True):
                # Auto-submit if not already submitted
                if not already_submitted:
                    app.update_user_answer(question_number, st.session_state.user_answer, correct_answer)
                st.session_state.show_explanation = True
        
        if st.session_state.show_explanation:
            # Show if the answer is correct or not
            if correct_answer and st.session_state.user_answer == correct_answer:
                st.success(f"🎉 Correct! You selected: **{st.session_state.user_answer}**", icon="✅")
            elif correct_answer:
                st.error(f"❌ Incorrect. You selected: **{st.session_state.user_answer}**. The correct answer is: **{correct_answer}**", icon="❌")
            else:
                st.info(f"You selected: **{st.session_state.user_answer}** (Could not determine correct answer)", icon="ℹ️")
            
            st.subheader("📝 Explanation:")
            # Add correct answer indication to explanation
            if correct_answer:
                st.info(f"**Correct Answer: {correct_answer}**", icon="🎯")
            st.markdown(explanation)
        
    # Manual correct answer input for questions where auto-detection failed
    if not correct_answer:
        st.markdown("---")
        st.warning("⚠️ Could not automatically determine the correct answer for this question.", icon="⚠️")
        st.subheader("🔧 Manual Answer Input")
        st.markdown("Please help by entering the correct answer:")
        
        manual_col1, manual_col2 = st.columns([2, 1])
        with manual_col1:
            manual_answer = st.selectbox(
                "Select the correct answer:",
                ["", "A", "B", "C", "D"],
                key=f"manual_answer_{question_number}"
            )
        
        with manual_col2:
            if manual_answer and st.button("💾 Save Answer", key=f"save_answer_{question_number}", type="secondary", use_container_width=True):
                # Store in both global answers and user's personal file
                app.store_correct_answer(question_number, manual_answer)
                app.update_user_answer(question_number, st.session_state.user_answer if st.session_state.user_answer else None, manual_answer)
                st.success(f"✅ Saved: {manual_answer}", icon="✅")
                # Update the cached data
                if f"question_{question_number}" in st.session_state.question_data_cache:
                    st.session_state.question_data_cache[f"question_{question_number}"]["correct_answer"] = manual_answer
                st.rerun()
    
    # Navigation section
    st.markdown("---")
    st.subheader("🧭 Navigation")
    
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    
    with nav_col1:
        if st.button("⬅️ Previous Question", disabled=(st.session_state.current_question_index == 0), use_container_width=True):
            st.session_state.current_question_index -= 1
            st.session_state.user_answer = None
            st.session_state.show_explanation = False
            st.rerun()
    
    with nav_col2:
        if st.button("➡️ Next Question", disabled=(st.session_state.current_question_index == total_questions - 1), use_container_width=True):
            st.session_state.current_question_index += 1
            st.session_state.user_answer = None
            st.session_state.show_explanation = False
            st.rerun()
    
    with nav_col3:
        # PDF viewing options in an expander
        with st.expander("📄 View Original PDF"):
            app.create_pdf_viewer_options(current_pdf, question_number)
    
    # Footer
    st.write("---")
    st.info("💡 **OCR Version:** This version uses Tesseract OCR to extract text from PDFs, which should handle formatting issues better than the standard PDF text extraction.")

if __name__ == "__main__":
    main() 
