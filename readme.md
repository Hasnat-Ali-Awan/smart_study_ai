📘 Smart Study AI
An intelligent, fully offline study assistant that allows you to upload documents (PDF, TXT, DOCX) and chat with them using local AI powered by Ollama. No internet required, no API keys needed!



✨ Features
📁 Document Upload: Support for PDF, TXT, and DOCX files

💬 AI Chat: Ask questions about your uploaded documents

🔒 Fully Offline: Uses Ollama for local AI processing

💾 Session Management: Organize documents by sessions

📊 Database Storage: SQLite backend for persistent storage

🎨 Modern UI: Clean, dark-themed Streamlit interface

🚀 Quick Start
Prerequisites
Python 3.8+

Ollama installed locally

Installation
Clone the repository

bash
git clone https://github.com/Hasnat-Ali-Awan/smart_study_ai.git
cd smart-study-ai
Create virtual environment (Recommended)

bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
Install Python dependencies

bash
pip install -r requirements.txt
Install and Setup Ollama

bash
# Download and install Ollama from https://ollama.ai/

# Pull the AI model (using a lightweight model)
ollama pull llama3.2:1b
🖥️ Running the Application
Start the app

bash
streamlit run main.py
Open your browser

The app will open automatically at http://localhost:8501

If not, manually navigate to the URL shown in terminal

Start using Smart Study AI

Upload study materials (PDF, TXT, DOCX)

Create or switch between sessions

Ask questions about your documents

View chat history

📁 Project Structure
text
smart-study-ai/
├── main.py              # Main Streamlit application
├── database.py          # SQLite database operations
├── backend.py           # Ollama AI integration
├── utils.py             # File processing utilities
├── prompt.py            # AI prompt templates
├── requirements.txt     # Python dependencies
├── data/               # Database and uploaded files
└── README.md           # This file
🔧 Configuration
Models
By default, the app uses llama3.2:1b (1 billion parameter model). To use a different model:

Pull your preferred model:

bash
ollama pull llama3.2:3b  # Larger model
# or
ollama pull mistral      # Alternative model
Update backend.py:

python
# Change this line in backend.py
stream = ollama.generate(
    model="llama3.2:1b",  # ← Change to your model
    prompt=prompt,
    stream=True,
)
Database Location
Database: data/study_ai.db

Uploaded files: data/uploads/

🐛 Troubleshooting
Common Issues
"Ollama not found" error

Ensure Ollama is installed and running

Check if ollama serve is running in background

Database errors

Reset the database: python reset.py

Or manually delete data/ folder and restart

File upload issues

Check file format (PDF, TXT, DOCX only)

Ensure file is not corrupted

Try with a smaller file first

Reset Application
bash
python reset_database.py
📚 Usage Guide
Upload Documents

Click "Upload Documents"

Select PDF/TXT/DOCX files

Wait for processing (text extraction)

Create Sessions

Click "New Session" in sidebar

Name your session

Switch between sessions anytime

Chat with Documents

Type your question in the chat box

Click "Generate"

AI responds using document content only

Manage Files

View uploaded files in sidebar

Delete unwanted files

Clear entire sessions

🛠️ Development
Adding New Features
Fork the repository

Create a feature branch

Make your changes

Test thoroughly

Submit pull request

Running Tests
bash
# Add your tests in tests/ directory
pytest tests/
🤝 Contributing
Contributions are welcome! Please:

Fork the repository

Create a feature branch

Commit your changes

Push to the branch

Open a Pull Request

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments
Ollama for local AI capabilities

Streamlit for the web framework

SQLite for lightweight database

All open-source libraries used in this project

📞 Support
For issues and questions:

Check Troubleshooting section

Open a GitHub Issue

Check existing issues for solutions

⭐ Star this repo if you find it useful!

Happy Studying! 📚✨
