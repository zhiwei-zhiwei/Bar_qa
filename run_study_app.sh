#!/bin/bash

# Law Study Tool Launcher Script
# This script activates the virtual environment and starts the Streamlit app

echo "🚀 Starting Law Study Tool..."
echo "📚 Activating virtual environment..."

# Check if virtual environment exists
if [ ! -d "pdf_env" ]; then
    echo "❌ Virtual environment 'pdf_env' not found!"
    echo "Please run: python -m venv pdf_env"
    echo "Then install dependencies: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source pdf_env/bin/activate

# Check if requirements are installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing requirements..."
    pip install -r requirements.txt
fi

# Check if questions directory exists
if [ ! -d "all_questions" ]; then
    echo "❌ Questions directory 'all_questions' not found!"
    echo "Please ensure your PDF files are in the 'all_questions' directory"
    exit 1
fi

# Count number of questions
question_count=$(ls all_questions/question_*.pdf 2>/dev/null | wc -l)
echo "📖 Found $question_count question files"

if [ $question_count -eq 0 ]; then
    echo "❌ No question PDF files found in 'all_questions' directory!"
    echo "Please add your question PDF files named as: question_1.pdf, question_2.pdf, etc."
    exit 1
fi

echo "✅ All checks passed!"
echo "🌐 Starting Streamlit application..."
echo "📱 Open your browser to: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Start Streamlit app
streamlit run study_app.py 