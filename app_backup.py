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
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        color: #1565c0;
    }
    .ai-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
        color: #6a1b9a;
    }
    .document-info {
        background-color: #f8f9fa;
        color: #333333;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'pdf_processor' not in st.session_state:
        st.session_state.pdf_processor = PDFProcessor()
    
    if 'embeddings_handler' not in st.session_state:
        st.session_state.embeddings_handler = EmbeddingsHandler()
    
    if 'llm_handler' not in st.session_state:
        st.session_state.llm_handler = LLMHandler()
    
    if 'processed_documents' not in st.session_state:
        st.session_state.processed_documents = []
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'vector_index_built' not in st.session_state:
        st.session_state.vector_index_built = False

def sidebar_controls():
    """Create sidebar with controls and settings"""
    st.sidebar.header("📚 PDF Chatbot")
    
    # API Key Status
    st.sidebar.subheader("🔑 API Status")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and len(api_key) > 10:
        st.sidebar.warning("🟡 Demo Mode Active")
        st.sidebar.info("API key found but running offline to save credits")
        if st.sidebar.button("💡 About Full Mode"):
            st.sidebar.write("Add credits to OpenAI account for:")
            st.sidebar.write("• Live AI responses")
            st.sidebar.write("• Advanced analysis")
            st.sidebar.write("• Smart embeddings")
    elif api_key:
        st.sidebar.error("❌ Invalid API Key")
        st.sidebar.info("Please check your .env file")
    else:
        st.sidebar.info("🆓 Demo Mode")
        st.sidebar.write("Working offline - no API key needed!")
    
    # Document Upload Section
    st.sidebar.subheader("📁 Upload Documents")
    uploaded_files = st.sidebar.file_uploader(
        "Choose PDF files",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload one or more PDF documents to analyze"
    )
    
    # Processing Controls
    chunk_size = st.sidebar.slider(
        "Chunk Size",
        min_value=500,
        max_value=2000,
        value=1000,
        step=100,
        help="Size of text chunks for processing"
    )
    
    # Process Documents Button
    if uploaded_files and st.sidebar.button("🔄 Process Documents"):
        process_documents(uploaded_files, chunk_size)
    
    # LLM Settings
    st.sidebar.subheader("🤖 AI Settings")
    
    model_choice = st.sidebar.selectbox(
        "Model",
        ["demo-mode", "gpt-3.5-turbo", "gpt-4"],
        help="Choose the AI model to use"
    )
    
    temperature = st.sidebar.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Controls response creativity (0=focused, 1=creative)"
    )
    
    max_tokens = st.sidebar.slider(
        "Max Response Length",
        min_value=100,
        max_value=2000,
        value=1000,
        step=100,
        help="Maximum length of AI responses"
    )
    
    prompt_type = st.sidebar.selectbox(
        "Response Type",
        ["default", "financial", "summary"],
        help="Choose specialized prompts for different use cases"
    )
    
    # Update LLM handler settings
    st.session_state.llm_handler.model = model_choice
    
    return {
        'temperature': temperature,
        'max_tokens': max_tokens,
        'prompt_type': prompt_type
    }

def process_documents(uploaded_files: List, chunk_size: int):
    """Process uploaded PDF documents"""
    with st.spinner("Processing documents..."):
        # Process PDFs
        results = st.session_state.pdf_processor.process_multiple_pdfs(
            uploaded_files, chunk_size
        )
        
        if results:
            st.session_state.processed_documents = results
            
            # Build vector index
            st.session_state.embeddings_handler.build_vector_index(results)
            st.session_state.vector_index_built = True
            
            st.success(f"Successfully processed {len(results)} documents!")
            
            # Show document statistics
            display_document_stats(results)
        else:
            st.error("No documents were successfully processed.")

def display_document_stats(documents: List[Dict]):
    """Display statistics about processed documents"""
    st.subheader("📊 Document Statistics")
    
    total_words = sum(doc['word_count'] for doc in documents)
    total_chunks = sum(doc['chunk_count'] for doc in documents)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Documents", len(documents))
    
    with col2:
        st.metric("Total Words", f"{total_words:,}")
    
    with col3:
        st.metric("Total Chunks", total_chunks)
    
    with col4:
        avg_words = total_words // len(documents) if documents else 0
        st.metric("Avg Words/Doc", f"{avg_words:,}")
    
    # Document details
    with st.expander("📄 Document Details"):
        for doc in documents:
            st.markdown(f"""
            <div class="document-info">
                <strong>📁 {doc['filename']}</strong><br>
                Words: {doc['word_count']:,} | Characters: {doc['char_count']:,} | Chunks: {doc['chunk_count']}
            </div>
            """, unsafe_allow_html=True)

def display_chat_interface(settings: Dict):
    """Display the main chat interface"""
    st.markdown("<h1 class='main-header'>🤖 PDF Chatbot</h1>", unsafe_allow_html=True)
    
    if not st.session_state.vector_index_built:
        st.info("👆 Please upload and process PDF documents using the sidebar to start chatting!")
        return
    
    # Display index statistics
    stats = st.session_state.embeddings_handler.get_index_stats()
    st.info(f"📚 Ready to answer questions about {stats['unique_documents']} documents with {stats['total_chunks']} text chunks")
    
    # Chat input
    user_question = st.text_input(
        "Ask a question about your documents:",
        placeholder="e.g., What are the main topics discussed in the documents?",
        key="user_input"
    )
    
    # Quick question buttons
    st.markdown("**💡 Quick Questions:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Summarize documents"):
            user_question = "Please provide a comprehensive summary of all the uploaded documents."
    
    with col2:
        if st.button("🔍 Key findings"):
            user_question = "What are the key findings and main points from these documents?"
    
    with col3:
        if st.button("📊 Important data"):
            user_question = "What are the most important data points, statistics, or metrics mentioned?"
    
    # Process question
    if user_question:
        process_question(user_question, settings)
    
    # Display chat history
    display_chat_history()
    
    # Clear chat button
    if st.session_state.chat_history and st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

def process_question(question: str, settings: Dict):
    """Process user question and generate response"""
    with st.spinner("🤔 Thinking..."):
        # Get relevant context
        context = st.session_state.embeddings_handler.get_context_for_query(question)
        
        # Generate response
        response = st.session_state.llm_handler.generate_response(
            query=question,
            context=context,
            temperature=settings['temperature'],
            max_tokens=settings['max_tokens'],
            prompt_type=settings['prompt_type']
        )
        
        if response:
            # Add to chat history
            chat_entry = {
                'timestamp': time.time(),
                'question': question,
                'response': response,
                'context': context,
                'settings': settings.copy()
            }
            st.session_state.chat_history.append(chat_entry)
            
            # Generate follow-up questions
            follow_ups = st.session_state.llm_handler.generate_follow_up_questions(
                question, response, context
            )
            if follow_ups:
                chat_entry['follow_ups'] = follow_ups
            
            st.rerun()

def display_chat_history():
    """Display chat history with messages"""
    if not st.session_state.chat_history:
        return
    
    st.subheader("💬 Chat History")
    
    for i, entry in enumerate(reversed(st.session_state.chat_history)):
        # User message
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>👤 You:</strong><br>
            {entry['question']}
        </div>
        """, unsafe_allow_html=True)
        
        # AI response
        st.markdown(f"""
        <div class="chat-message ai-message">
            <strong>🤖 AI Assistant:</strong><br>
            {entry['response']}
        </div>
        """, unsafe_allow_html=True)
        
        # Follow-up questions (display only - no buttons)
        if 'follow_ups' in entry and entry['follow_ups']:
            st.markdown("**💡 Suggested follow-up questions:**")
            for follow_up in entry['follow_ups']:
                st.markdown(f"• {follow_up}")
            st.markdown("*Copy and paste any question above into the input box*")
        
        # Show context in expander
        with st.expander(f"📖 View source context for this answer"):
            st.text(entry['context'])
        
        st.markdown("---")

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Create sidebar controls and get settings
    settings = sidebar_controls()
    
    # Main chat interface
    display_chat_interface(settings)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "Built with ❤️ using Streamlit, OpenAI, and Sentence Transformers | "
        "Upload PDFs and start asking questions!"
    )

if __name__ == "__main__":
    main() 
