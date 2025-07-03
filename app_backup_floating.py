import streamlit as st
import os
from typing import List, Dict
import time
import json
from datetime import datetime
import io

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
# Updated CSS with fixed floating input
st.markdown("""
<style>
    /* Remove default padding and margins */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 120px; /* Space for fixed input */
        max-width: 1200px;
    }
    
    /* Hide streamlit elements */
    .stApp > header {display: none;}
    .stApp > footer {display: none;}
    #MainMenu {display: none;}
    
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
    
    /* FIXED/FLOATING INPUT AREA */
    .floating-input {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-top: 1px solid #e2e8f0;
        padding: 1rem;
        z-index: 1000;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
    }
    
    /* Quick questions floating */
    .floating-questions {
        position: fixed;
        bottom: 80px;
        left: 0;
        right: 0;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-top: 1px solid #e2e8f0;
        padding: 0.5rem 1rem;
        z-index: 999;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }
    
    /* Input styling */
    .stTextInput input {
        border-radius: 25px;
        border: 2px solid #e2e8f0;
        padding: 12px 20px;
        font-size: 14px;
        transition: all 0.3s ease;
        background: white;
    }
    
    .stTextInput input:focus {
        border-color: #4f46e5;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    }
    
    /* Send button styling */
    .stButton > button {
        border-radius: 25px;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        border: none;
        color: white;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
        min-height: 48px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4);
    }
    
    /* Quick question buttons */
    .quick-btn {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 8px 16px;
        margin: 0 5px;
        font-size: 13px;
        color: #374151;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .quick-btn:hover {
        background: #f8fafc;
        border-color: #4f46e5;
        color: #4f46e5;
    }
    
    /* Remove unwanted margins from containers */
    .element-container {
        margin-bottom: 0 !important;
    }
    
    /* Save section styling */
    .save-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin: 1rem 0;
    }
    
    /* Welcome message improvements */
    .welcome-container {
        min-height: 60vh;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Chat container */
    .chat-container {
        min-height: 60vh;
        padding-bottom: 140px; /* Extra space for floating input */
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONVERSATION SAVE/LOAD FUNCTIONS
# ============================================

def export_conversation_text() -> str:
    """Export conversation as formatted text"""
    if not st.session_state.messages:
        return "No conversation to export."
    
    # Get document info
    doc_info = st.session_state.get('doc_info', {})
    doc_name = doc_info.get('filename', 'Unknown Document')
    
    # Create header
    export_text = f"""PDF CHATBOT CONVERSATION EXPORT
=================================

Document: {doc_name}
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Messages: {len(st.session_state.messages)}

=================================

"""
    
    # Add conversation
    for i, msg in enumerate(st.session_state.messages, 1):
        role = "🤖 AI Assistant" if msg["role"] == "assistant" else "👤 You"
        export_text += f"[{i}] {role}:\n"
        export_text += f"{msg['content']}\n\n"
        export_text += "-" * 50 + "\n\n"
    
    export_text += f"""
=================================
End of Conversation Export
Generated by PDF Chatbot
=================================
"""
    
    return export_text

def export_conversation_json() -> str:
    """Export conversation as JSON"""
    if not st.session_state.messages:
        return "{}"
    
    doc_info = st.session_state.get('doc_info', {})
    
    export_data = {
        "export_info": {
            "timestamp": datetime.now().isoformat(),
            "document_name": doc_info.get('filename', 'Unknown'),
            "document_stats": {
                "word_count": doc_info.get('word_count', 0),
                "chunk_count": doc_info.get('chunk_count', 0)
            },
            "total_messages": len(st.session_state.messages)
        },
        "conversation": st.session_state.messages
    }
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)

def export_conversation_markdown() -> str:
    """Export conversation as Markdown"""
    if not st.session_state.messages:
        return "# No conversation to export"
    
    doc_info = st.session_state.get('doc_info', {})
    doc_name = doc_info.get('filename', 'Unknown Document')
    
    markdown_text = f"""# PDF Chatbot Conversation

**Document:** {doc_name}  
**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Messages:** {len(st.session_state.messages)}

---

"""
    
    for i, msg in enumerate(st.session_state.messages, 1):
        if msg["role"] == "user":
            markdown_text += f"## 👤 Question {i//2 + 1}\n\n{msg['content']}\n\n"
        else:
            markdown_text += f"## 🤖 AI Response\n\n{msg['content']}\n\n---\n\n"
    
    markdown_text += """
*Generated by PDF Chatbot*
"""
    
    return markdown_text

def save_conversation_sidebar():
    """Add save conversation options to sidebar"""
    if st.session_state.messages:
        st.sidebar.markdown("---")
        st.sidebar.subheader("💾 Save Conversation")
        
        # Save format selection
        save_format = st.sidebar.selectbox(
            "Export Format",
            ["Text (.txt)", "Markdown (.md)", "JSON (.json)"],
            help="Choose format for saving conversation"
        )
        
        # Generate filename
        doc_info = st.session_state.get('doc_info', {})
        doc_name = doc_info.get('filename', 'conversation')
        # Clean filename
        clean_doc_name = "".join(c for c in doc_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if save_format == "Text (.txt)":
            filename = f"chat_{clean_doc_name}_{timestamp}.txt"
            content = export_conversation_text()
            mime_type = "text/plain"
        elif save_format == "Markdown (.md)":
            filename = f"chat_{clean_doc_name}_{timestamp}.md"
            content = export_conversation_markdown()
            mime_type = "text/markdown"
        else:  # JSON
            filename = f"chat_{clean_doc_name}_{timestamp}.json"
            content = export_conversation_json()
            mime_type = "application/json"
        
        # Download button
        st.sidebar.download_button(
            label="📥 Download Conversation",
            data=content,
            file_name=filename,
            mime=mime_type,
            help=f"Download conversation as {save_format}",
            use_container_width=True
        )
        
        # Conversation stats
        if st.sidebar.button("📊 Show Stats", use_container_width=True):
            total_messages = len(st.session_state.messages)
            user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
            ai_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
            
            st.sidebar.metric("Total Messages", total_messages)
            st.sidebar.metric("Your Questions", user_messages) 
            st.sidebar.metric("AI Responses", ai_messages)
            
            # Calculate total characters
            total_chars = sum(len(m["content"]) for m in st.session_state.messages)
            st.sidebar.metric("Total Characters", f"{total_chars:,}")

def load_conversation_sidebar():
    """Add load conversation option to sidebar"""
    st.sidebar.subheader("📂 Load Conversation")
    
    uploaded_chat = st.sidebar.file_uploader(
        "Upload Previous Chat",
        type=['json'],
        help="Load a previously saved conversation (JSON format only)",
        key="chat_uploader"
    )
    
    if uploaded_chat:
        try:
            # Read the JSON file
            chat_data = json.loads(uploaded_chat.read().decode('utf-8'))
            
            if 'conversation' in chat_data:
                # Validate the format
                if isinstance(chat_data['conversation'], list):
                    # Show preview
                    st.sidebar.success(f"✅ Found {len(chat_data['conversation'])} messages")
                    
                    if 'export_info' in chat_data:
                        info = chat_data['export_info']
                        st.sidebar.info(f"📄 Document: {info.get('document_name', 'Unknown')}")
                        st.sidebar.info(f"📅 Date: {info.get('timestamp', 'Unknown')}")
                    
                    # Load button
                    if st.sidebar.button("🔄 Load This Conversation"):
                        st.session_state.messages = chat_data['conversation']
                        st.sidebar.success("✅ Conversation loaded!")
                        st.rerun()
                else:
                    st.sidebar.error("❌ Invalid conversation format")
            else:
                st.sidebar.error("❌ No conversation data found")
                
        except json.JSONDecodeError:
            st.sidebar.error("❌ Invalid JSON file")
        except Exception as e:
            st.sidebar.error(f"❌ Error loading file: {str(e)}")

# ============================================
# MAIN APPLICATION FUNCTIONS  
# ============================================

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
    """Enhanced sidebar with save/load functionality"""
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
    
    # Save/Load functionality
    save_conversation_sidebar()
    load_conversation_sidebar()

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

def show_conversation_controls():
    """Show conversation controls in main area"""
    if st.session_state.messages:
        st.markdown("---")
        st.markdown("### 💾 Conversation Controls")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Quick save button
            doc_info = st.session_state.get('doc_info', {})
            doc_name = doc_info.get('filename', 'conversation')
            clean_name = "".join(c for c in doc_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            st.download_button(
                "📥 Quick Save (TXT)",
                data=export_conversation_text(),
                file_name=f"chat_{clean_name}_{timestamp}.txt",
                mime="text/plain",
                help="Download conversation as text file",
                use_container_width=True
            )
        
        with col2:
            st.download_button(
                "📋 Save as Markdown",
                data=export_conversation_markdown(),
                file_name=f"chat_{clean_name}_{timestamp}.md",
                mime="text/markdown",
                help="Download conversation as Markdown",
                use_container_width=True
            )
        
        with col3:
            st.download_button(
                "📊 Save as JSON",
                data=export_conversation_json(),
                file_name=f"chat_{clean_name}_{timestamp}.json",
                mime="application/json", 
                help="Download conversation with metadata",
                use_container_width=True
            )
        
        with col4:
            # Show stats
            total_messages = len(st.session_state.messages)
            st.metric("Messages", total_messages)

def main():
    """Main app with fixed floating input"""
    initialize_session()
    sidebar()
    
    # Compact header (no extra space)
    st.markdown("""
    <div style='text-align: center; margin-bottom: 1rem; padding-top: 0;'>
        <h1 style='background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; font-size: 2.5rem;'>
            🤖 Smart PDF Chatbot
        </h1>
        <p style='color: #64748b; margin: 0.2rem 0; font-size: 1rem;'>Have intelligent conversations with your documents</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Document status (compact)
    if st.session_state.document_ready and st.session_state.doc_info:
        doc = st.session_state.doc_info
        st.markdown(f"""
        <div class="doc-status" style="margin-bottom: 1rem; padding: 0.8rem;">
            📄 <strong>{doc['filename']}</strong> Ready! • 📊 {doc['word_count']:,} words • {doc['chunk_count']} chunks
        </div>
        """, unsafe_allow_html=True)
    
    # Chat area (with proper container)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    show_chat()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Conversation controls (above floating input)
    show_conversation_controls()
    
    # FLOATING QUICK QUESTIONS
    st.markdown('<div class="floating-questions">', unsafe_allow_html=True)
    floating_quick_questions()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # FLOATING INPUT AREA
    st.markdown('<div class="floating-input">', unsafe_allow_html=True)
    floating_input_area()
    st.markdown('</div>', unsafe_allow_html=True)

def floating_quick_questions():
    """Floating quick questions bar"""
    if not st.session_state.document_ready:
        questions = ["How does this work?", "What can you analyze?", "Upload a document"]
    else:
        doc = st.session_state.doc_info
        if doc and 'annual' in doc['filename'].lower():
            questions = ["Key metrics?", "Financial highlights?", "Business strategy?"]
        elif doc and 'research' in doc['filename'].lower():
            questions = ["Research objective?", "Methodology?", "Key findings?"]
        else:
            questions = ["Summarize document", "Main topics?", "Key insights?"]
    
    st.markdown("**💡 Quick questions:**")
    cols = st.columns(len(questions))
    
    for i, q in enumerate(questions):
        with cols[i]:
            if st.button(q, key=f"floating_quick_{i}", use_container_width=True):
                # Store the question and trigger processing
                st.session_state.pending_question = q
                st.rerun()

def floating_input_area():
    """Fixed floating input area"""
    # Check for pending question from quick buttons
    pending_q = st.session_state.get('pending_question', '')
    if pending_q:
        # Clear the pending question
        del st.session_state.pending_question
        # Process it
        handle_question(pending_q)
        st.rerun()
    
    # Input row
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Message",
            placeholder="Ask anything about your document...",
            key="floating_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send = st.button("Send", use_container_width=True, key="floating_send")
    
    # Handle input
    if send and user_input:
        handle_question(user_input)
        # Clear the input by rerunning
        st.rerun()

if __name__ == "__main__":
    main()