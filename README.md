# 📚 Law Study Tool - MBE Practice Questions

A Streamlit-based study tool for practicing Multiple Choice Bar Examination (MBE) questions. This application reads PDF files containing legal questions and provides an interactive interface for studying.

## ✨ Features

- **Interactive Question Display**: Read questions from PDF files with clean formatting
- **Multiple Choice Interface**: Select answers using radio buttons (A, B, C, D)
- **Detailed Explanations**: View explanations after selecting an answer
- **Navigation**: 
  - Previous/Next buttons for sequential study
  - Sidebar dropdown to jump to any question
  - Progress indicator showing current position
- **PDF Access**: Download original PDF files for offline viewing
- **Session Management**: Maintains your progress within the session

## 🔧 Setup Instructions

### Prerequisites
- Python 3.7 or higher
- Virtual environment (recommended)

### Installation

1. **Clone or download this repository**

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv pdf_env
   source pdf_env/bin/activate  # On Windows: pdf_env\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure your PDF files are in the correct location**:
   - Place your question PDF files in the `all_questions/` directory
   - Files should be named in the format: `question_1.pdf`, `question_2.pdf`, etc.

## 🚀 Usage

### Starting the Application

1. **Activate your virtual environment**:
   ```bash
   source pdf_env/bin/activate  # On Windows: pdf_env\Scripts\activate
   ```

2. **Run the Streamlit app**:
   ```bash
   streamlit run study_app.py
   ```

3. **Open your browser** to the URL shown in the terminal (typically `http://localhost:8501`)

### Using the Study Tool

1. **Read the Question**: The main content area displays the current question
2. **Select Your Answer**: Choose from the multiple choice options (A, B, C, D)
3. **View Explanation**: Click "Show Explanation" to see the detailed explanation
4. **Navigate**: Use the Previous/Next buttons or the sidebar dropdown to move between questions
5. **Download PDF**: Click "View Original PDF" to download the original question file

### Navigation Options

- **Sequential Navigation**: Use Previous/Next buttons
- **Jump to Question**: Use the dropdown in the sidebar to go directly to any question
- **Progress Tracking**: Monitor your progress with the progress bar

## 📁 File Structure

```
janet/
├── study_app.py           # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── all_questions/        # Directory containing question PDFs
│   ├── question_1.pdf
│   ├── question_2.pdf
│   └── ...
├── pdf_env/              # Virtual environment (if using)
└── split_pdf.py          # Utility for splitting PDFs (optional)
```

## 🔍 How It Works

The application:

1. **Scans** the `all_questions/` directory for PDF files
2. **Extracts** text content from each PDF using PyPDF2
3. **Parses** questions and explanations (separated by "Explanation:")
4. **Identifies** multiple choice options (A., B., C., D.)
5. **Displays** questions with interactive interface
6. **Manages** user selections and navigation state

## 🛠️ Troubleshooting

### Common Issues

1. **"No PDF files found"**:
   - Ensure PDF files are in the `all_questions/` directory
   - Check that files are named correctly (`question_*.pdf`)

2. **"Error reading PDF"**:
   - Verify PDF files are not corrupted
   - Ensure PDF files contain extractable text

3. **"Could not parse question text"**:
   - Check that PDF contains properly formatted questions
   - Ensure questions have A., B., C., D. options

### Dependencies

Main dependencies include:
- `streamlit`: Web application framework
- `PyPDF2`: PDF processing library
- `pandas`: Data manipulation (if needed)

## 🎯 Tips for Effective Study

1. **Read Carefully**: Take time to understand each question before selecting
2. **Use Explanations**: Always read the explanation to understand the reasoning
3. **Track Progress**: Use the progress indicator to monitor your study session
4. **Review Difficult Questions**: Use the sidebar to revisit challenging questions
5. **Save Original PDFs**: Download PDFs for offline study when needed

## 🔄 Updating Questions

To add new questions:
1. Place new PDF files in the `all_questions/` directory
2. Name them following the pattern: `question_[number].pdf`
3. Restart the application to load new questions

## 📞 Support

If you encounter issues:
1. Check that all dependencies are installed correctly
2. Verify PDF file format and location
3. Ensure your Python environment is properly set up
4. Check the terminal for any error messages

---

**Happy Studying! 📖✨** 