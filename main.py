import streamlit as st
import os
import json
from datetime import datetime
from utils import process_file_upload
from backend import generate_study_response
from database import db

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Smart Study AI",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CUSTOM CSS =================
st.markdown("""
<style>
/* Reset default styles */
.stApp {
    background-color: #0f172a;
}

/* Main container */
.main-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
}

/* Header */
.app-header {
    text-align: center;
    padding: 2rem 0;
    border-bottom: 2px solid #1e293b;
    margin-bottom: 2rem;
}

/* Chat messages */
.chat-message {
    padding: 1.2rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    animation: fadeIn 0.3s ease-in;
}

.user-message {
    background-color: rgba(30, 58, 138, 0.3);
    border-left: 4px solid #3b82f6;
    margin-left: 10%;
}

.ai-message {
    background-color: rgba(30, 41, 59, 0.5);
    border-left: 4px solid #10b981;
    margin-right: 10%;
}

/* Session cards */
.session-card {
    padding: 0.8rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    border: 1px solid #334155;
    transition: all 0.2s;
}

.session-card:hover {
    background-color: #1e293b;
    transform: translateX(5px);
}

.session-active {
    border-color: #10b981;
    background-color: rgba(16, 185, 129, 0.1);
}

/* File items */
.file-item {
    padding: 0.6rem;
    border-radius: 6px;
    background-color: #1e293b;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}

/* Buttons */
.stButton > button {
    transition: all 0.2s;
    border-radius: 8px;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.streaming-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #10b981;
    margin-left: 4px;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* Responsive */
@media (max-width: 768px) {
    .user-message, .ai-message {
        margin-left: 0;
        margin-right: 0;
    }
}
</style>
""", unsafe_allow_html=True)

# ================= SESSION STATE =================
def init_session_state():
    """Initialize session state variables"""
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True
        
        # Initialize with empty values
        st.session_state.current_session = None
        st.session_state.current_session_id = None
        st.session_state.session_files = []
        st.session_state.session_chats = []
        st.session_state.all_sessions = []
        st.session_state.streaming = False
        st.session_state.current_response = ""
        
        # Load data
        load_initial_data()

def load_initial_data():
    """Load initial data from database"""
    try:
        # Get active session
        active_session = db.get_active_session()
        
        if active_session:
            st.session_state.current_session = active_session
            st.session_state.current_session_id = active_session['id']
            st.session_state.session_files = db.get_session_files(active_session['id'])
            st.session_state.session_chats = db.get_session_chats(active_session['id'])
        else:
            # Create default session
            session_id = db.create_session("Default Session")
            st.session_state.current_session = db.get_active_session()
            st.session_state.current_session_id = session_id
            st.session_state.session_files = []
            st.session_state.session_chats = []
        
        # Load all sessions
        st.session_state.all_sessions = db.get_all_sessions()
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Initialize with empty values
        st.session_state.current_session = None
        st.session_state.current_session_id = None
        st.session_state.session_files = []
        st.session_state.session_chats = []
        st.session_state.all_sessions = []

# Initialize session state
init_session_state()

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## 📘 Smart Study AI")
    st.markdown("---")
    
    # Session Management
    st.markdown("### 📁 Sessions")
    
    # New session button
    if st.button("➕ New Session", use_container_width=True):
        session_name = st.text_input("Session name:", value=f"Session {len(st.session_state.all_sessions) + 1}")
        if st.button("Create", key="create_session"):
            if session_name:
                session_id = db.create_session(session_name)
                load_initial_data()
                st.rerun()
    
    # List sessions
    if st.session_state.all_sessions:
        for session in st.session_state.all_sessions:
            is_active = session['id'] == st.session_state.current_session_id
            
            col1, col2 = st.columns([3, 1])
            with col1:
                session_style = "session-active" if is_active else ""
                st.markdown(f"<div class='session-card {session_style}'>", unsafe_allow_html=True)
                st.markdown(f"**{session['session_name']}**")
                st.caption(f"📁 {session['file_count']} files | 💬 {session['chat_count']} chats")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                if not is_active:
                    if st.button("→", key=f"load_{session['id']}"):
                        if db.set_active_session(session['id']):
                            load_initial_data()
                            st.rerun()
                else:
                    st.markdown("**Active**")
    else:
        st.info("No sessions yet")
    
    # Files
    st.markdown("---")
    st.markdown("### 📄 Files")
    
    if st.session_state.session_files:
        for file in st.session_state.session_files[:5]:
            with st.expander(f"📄 {file['filename'][:20]}...", expanded=False):
                st.caption(f"Size: {file['filesize']/1024:.1f} KB")
                if st.button("Delete", key=f"del_{file['id']}"):
                    if db.delete_file(file['id']):
                        load_initial_data()
                        st.rerun()
    else:
        st.info("No files uploaded")
    
    # Stats
    st.markdown("---")
    stats = db.get_stats()
    st.markdown("### 📊 Statistics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sessions", stats['total_sessions'])
        st.metric("Files", stats['total_files'])
    with col2:
        st.metric("Chats", stats['total_chats'])
        st.metric("Storage", f"{stats['total_size']/1024/1024:.1f} MB")

# ================= MAIN CONTENT =================
# Header
st.markdown("<div class='app-header'>", unsafe_allow_html=True)
st.markdown("# 📘 Smart Study AI")
st.markdown("### Upload documents and chat with your AI study assistant")
st.markdown("</div>", unsafe_allow_html=True)

# Current session info
if st.session_state.current_session:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"**Active Session:** {st.session_state.current_session['session_name']} | "
                f"📁 {len(st.session_state.session_files)} files | "
                f"💬 {len(st.session_state.session_chats)} chats")
    with col2:
        if st.button("🔄 Refresh"):
            load_initial_data()
            st.rerun()

# File Upload
st.markdown("---")
st.markdown("## 📤 Upload Documents")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["pdf", "txt", "docx"],
    key="file_uploader"
)

if uploaded_file:
    with st.spinner("Processing file..."):
        try:
            result = process_file_upload(uploaded_file)
            if result:
                st.success(f"✅ Uploaded: {uploaded_file.name}")
                load_initial_data()
                
                # Show preview
                with st.expander("📝 Preview", expanded=False):
                    content = result['content']
                    preview = content[:1000] + ("..." if len(content) > 1000 else "")
                    st.text_area("Extracted text", preview, height=150, disabled=True)
        except Exception as e:
            st.error(f"Error uploading file: {e}")

# Chat History
st.markdown("---")
st.markdown("## 💬 Chat History")

if st.session_state.session_chats:
    for chat in st.session_state.session_chats:
        # User message
        st.markdown(
            f"""
            <div class='chat-message user-message'>
            <div style='color: #93c5fd; font-weight: bold;'>You:</div>
            <div style='margin: 0.5rem 0;'>{chat['question']}</div>
            <div style='font-size: 0.8rem; color: #9ca3af;'>
            {chat['created_at'][:16]}
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # AI response
        st.markdown(
            f"""
            <div class='chat-message ai-message'>
            <div style='color: #34d399; font-weight: bold;'>AI:</div>
            <div style='margin: 0.5rem 0;'>{chat['answer']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.info("No conversations yet. Upload a document and ask a question!")

# Question Input
st.markdown("---")
st.markdown("### Ask a Question")

question = st.text_area(
    "Your question:",
    height=100,
    placeholder="Ask anything about your uploaded documents...",
    key="question_input"
)

col1, col2 = st.columns([1, 5])
with col1:
    generate_disabled = not (question and st.session_state.session_files)
    generate_btn = st.button("🚀 Generate", type="primary", 
                           disabled=generate_disabled, use_container_width=True)

# Generate Response
if generate_btn and question:
    if not st.session_state.session_files:
        st.warning("Please upload a document first!")
        st.stop()
    
    try:
        # Get content
        session_content = db.get_session_content(st.session_state.current_session_id)
        
        if not session_content or len(session_content.strip()) < 10:
            st.error("No readable content found. Please upload valid documents.")
            st.stop()
        
        # Display user question
        st.markdown(
            f"""
            <div class='chat-message user-message'>
            <div style='color: #93c5fd; font-weight: bold;'>You:</div>
            <div>{question}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Create response container
        response_container = st.empty()
        
        # Stream response
        full_response = ""
        st.session_state.streaming = True
        
        try:
            for token in generate_study_response(session_content, question):
                if not st.session_state.streaming:
                    break
                
                full_response += token
                
                # Update display
                response_container.markdown(
                    f"""
                    <div class='chat-message ai-message'>
                    <div style='color: #34d399; font-weight: bold;'>AI:</div>
                    <div>{full_response}<span class='streaming-dot'></span></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Final display without streaming dot
            if full_response:
                response_container.markdown(
                    f"""
                    <div class='chat-message ai-message'>
                    <div style='color: #34d399; font-weight: bold;'>AI:</div>
                    <div>{full_response}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Save to database
                db.add_chat(st.session_state.current_session_id, question, full_response)
                
                # Refresh data
                load_initial_data()
                st.success("✓ Response saved!")
        
        except Exception as e:
            st.error(f"Error generating response: {e}")
        
        finally:
            st.session_state.streaming = False
    
    except Exception as e:
        st.error(f"Error: {e}")

# Database Management
with st.expander("🔧 Database Tools", expanded=False):
    tab1, tab2 = st.tabs(["Clear Data", "Export"])
    
    with tab1:
        st.warning("⚠️ This will delete ALL data!")
        
        if st.checkbox("I understand this cannot be undone"):
            if st.button("🗑️ DELETE ALL DATA", type="primary"):
                try:
                    if db.clear_all_data():
                        # Clear session state
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        
                        st.success("All data cleared! Refreshing...")
                        st.rerun()
                    else:
                        st.error("Failed to clear data")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with tab2:
        if st.button("📤 Export Current Session"):
            try:
                export_data = {
                    'session': st.session_state.current_session,
                    'files': st.session_state.session_files,
                    'chats': st.session_state.session_chats,
                    'exported_at': datetime.now().isoformat()
                }
                
                st.download_button(
                    "📥 Download JSON",
                    json.dumps(export_data, indent=2),
                    f"session_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json"
                )
            except Exception as e:
                st.error(f"Export error: {e}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #64748b; padding: 2rem 0;'>
    <strong>🔒 Fully Offline • 📚 Academic Use • 🚀 Powered by Ollama</strong><br>
    Smart Study AI - Your personal study assistant
    </div>
    """,
    unsafe_allow_html=True
)