import streamlit as st
import os
from typing import List, Dict
import time

# Import our custom modules
from utils.pdf_processor import PDFProcessor
from utils.embeddings import EmbeddingsHandler
from utils.llm_handler import LLMHandler

# Page configuration
st.set_page_config(
    page_title="PDF Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean CSS styling
st.markdown("""
<style>
    /* Clean layout */
    .main .block-container {
        padding-top: 1rem;
        max-width: 1200px;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1.2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .user-message {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        margin-left: 20%;
    }
    
    .ai-message {
        background: #f8fafc;
        color: #1e293b;
        border: 1px solid #e2e8f0;
        margin-right: 20%;
    }
    
    /* Document status */
    .doc-status {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    /* Input area */
    .input-section {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 15px;
        padding: 1rem;
        margin-top: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        background: white;
        color: #374151;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background: #f3f4f6;
        border-color: #4f46e5;
    }
    
    /* Primary button */
    .primary-btn {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session():
    """Initialize session state"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'document_ready' not in st.session_state:
        st.session_state.document_ready = False
    if 'doc_info' not in st.session_state:
        st.session_state.doc_info = None
    if 'embeddings' not in st.session_state:
        st.session_state.embeddings = None
    if 'llm' not in st.session_state:
        st.session_state.llm = LLMHandler()
    if 'pdf_proc' not in st.session_state:
        st.session_state.pdf_proc = PDFProcessor()

def sidebar():
    """Simple sidebar"""
    st.sidebar.title("🤖 PDF Chatbot")
    
    # Status
    st.sidebar.subheader("📊 Status")
    if st.session_state.document_ready:
        st.sidebar.success("✅ Document Ready")
        if st.session_state.doc_info:
            st.sidebar.info(f"📄 {st.session_state.doc_info['filename']}")
            st.sidebar.info(f"📝 {st.session_state.doc_info['word_count']:,} words")
    else:
        st.sidebar.info("📤 Upload a PDF to start")
    
    # Upload
    st.sidebar.subheader("📁 Upload")
    uploaded_file = st.sidebar.file_uploader("Choose PDF", type=['pdf'])
    
    if uploaded_file and not st.session_state.document_ready:
        if process_pdf(uploaded_file):
            st.rerun()
    
    # Controls
    st.sidebar.subheader("🛠️ Controls")
    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    if st.sidebar.button("🔄 New Document"):
        reset_session()
        st.rerun()

def process_pdf(file):
    """Process uploaded PDF"""
    try:
        with st.spinner("Processing PDF..."):
            # Process
            result = st.session_state.pdf_proc.process_pdf(file, chunk_size=1000)
            if not result:
                st.error("Failed to process PDF")
                return False
            
            # Create embeddings
            embeddings = EmbeddingsHandler()
            embeddings.build_vector_index([result])
            
            # Store
            st.session_state.embeddings = embeddings
            st.session_state.doc_info = result
            st.session_state.document_ready = True
            
            # Add welcome message
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"✅ **{result['filename']}** processed successfully!\n\n📊 **{result['word_count']:,} words** • **{result['chunk_count']} chunks**\n\nI'm ready to answer questions about your document!"
            })
            
            return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def reset_session():
    """Reset for new document"""
    st.session_state.messages = []
    st.session_state.document_ready = False
    st.session_state.doc_info = None
    st.session_state.embeddings = None

def show_chat():
    """Display chat messages"""
    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border-radius: 15px; margin: 2rem 0;'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>🤖</div>
            <h2 style='color: #1e293b; margin-bottom: 1rem;'>Welcome to PDF Chatbot!</h2>
            <p style='color: #64748b; font-size: 1.1rem;'>Upload a PDF document to start an intelligent conversation about its content.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Show messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>You:</strong><br>{msg["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message ai-message">
                <strong>🤖 Assistant:</strong><br>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(msg["content"])

def quick_questions():
    """Show quick question buttons"""
    if not st.session_state.document_ready:
        questions = ["How does this work?", "What can you analyze?", "Upload a document"]
    else:
        # Dynamic based on document
        doc = st.session_state.doc_info
        if doc and 'annual' in doc['filename'].lower():
            questions = ["What are the key metrics?", "Financial highlights?", "Business strategy?"]
        elif doc and 'research' in doc['filename'].lower():
            questions = ["What's the objective?", "Show methodology", "Key findings?"]
        else:
            questions = ["Summarize document", "Main topics?", "Key insights?"]
    
    st.markdown("**💡 Quick questions:**")
    cols = st.columns(len(questions))
    
    for i, q in enumerate(questions):
        with cols[i]:
            if st.button(q, key=f"quick_{i}"):
                return q
    return None

def handle_question(question):
    """Process user question"""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})
    
    if not st.session_state.document_ready:
        response = """I need you to upload a PDF document first! 

Use the sidebar to upload any PDF file, and I'll analyze it for you. I can help with:
• Research papers
• Business reports  
• Technical manuals
• Legal documents
• And more!"""
    else:
        try:
            # Get context
            context = st.session_state.embeddings.get_context_for_query(question, max_chunks=3)
            
            # Generate response
            response = st.session_state.llm.generate_response(
                query=question,
                context=context,
                prompt_type="default"
            )
            
            if not response:
                response = "I couldn't generate a response. Please try rephrasing your question."
        except Exception as e:
            response = f"Error: {e}. Please try again."
    
    # Add AI response
    st.session_state.messages.append({"role": "assistant", "content": response})

def main():
    """Main app"""
    initialize_session()
    sidebar()
    
    # Header
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;'>
            🤖 Smart PDF Chatbot
        </h1>
        <p style='color: #64748b; margin: 0.5rem 0;'>Have intelligent conversations with your documents</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Document status
    if st.session_state.document_ready and st.session_state.doc_info:
        doc = st.session_state.doc_info
        st.markdown(f"""
        <div class="doc-status">
            📄 <strong>{doc['filename']}</strong> Ready!<br>
            📊 {doc['word_count']:,} words • {doc['chunk_count']} chunks
        </div>
        """, unsafe_allow_html=True)
    
    # Chat area
    show_chat()
    
    # Input section
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    
    # Quick questions
    quick_q = quick_questions()
    
    # Input
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(
            "Ask anything about your document...",
            placeholder="What would you like to know?",
            key="user_input",
            label_visibility="collapsed"
        )
    with col2:
        send = st.button("Send", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle input
    if (send and user_input) or quick_q:
        question = quick_q if quick_q else user_input
        handle_question(question)
        st.rerun()

if __name__ == "__main__":
    main()