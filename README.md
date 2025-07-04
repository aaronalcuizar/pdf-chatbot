# PDF Chatbot - Intelligent Document Analysis

A sophisticated Streamlit application that enables users to upload PDF documents and engage in intelligent conversations about their content using ChatGPT integration.

## Features

### Core Functionality
- **PDF Upload & Processing**: Seamless PDF document upload with intelligent text extraction
- **Intelligent Q&A**: Ask questions about document content with context-aware responses
- **Dynamic Document Analysis**: Automatically detects document type and adapts responses
- **Interactive Chat Interface**: Clean, ChatGPT-style conversation interface

### Advanced Features
- **Smart Text Chunking**: Optimal document segmentation for better context retrieval
- **Vector Embeddings**: Efficient similarity search using FAISS or text-based search
- **Multi-Document Support**: Handle various document types (research papers, business reports, etc.)
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Quick Start

### Prerequisites
- Python 3.11+
- Git
- OpenAI API key (optional, demo mode available)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/aaronalcuizar/pdf-chatbot.git
cd pdf-chatbot
```

2. **Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux  
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment (optional)**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key for full functionality
```

5. **Run the application**
```bash
streamlit run app.py
```

6. **Open browser**
Navigate to `http://localhost:8501`

## Usage Guide

### 1. Upload Document
- Use the sidebar to upload any PDF document
- Supported formats: PDF files up to 200MB
- Processing takes 10-30 seconds depending on document size

### 2. Ask Questions
- Type questions in the chat input
- Use quick suggestion buttons for common queries
- Ask follow-up questions for deeper analysis

### 3. Analyze Responses
- View AI-generated responses with source context
- Check "View source context" to see relevant document sections
- Use suggested follow-up questions to explore further

### Example Questions
- "What is this document about?"
- "Summarize the key findings"
- "What are the main recommendations?"
- "Extract key financial metrics"

## Architecture

### System Design
```
User Input → PDF Processing → Text Chunking → Embeddings → LLM → Response
     ↓
Streamlit UI ← Response Formatting ← Context Retrieval ← Vector Search
```

### Components

#### PDF Processor (`utils/pdf_processor.py`)
- Extracts text from PDF files using PyMuPDF
- Implements intelligent text cleaning and preprocessing
- Splits documents into optimal chunks with overlap for context preservation

#### Embeddings Handler (`utils/embeddings.py`)
- Creates vector embeddings for semantic search
- Implements both OpenAI embeddings and text-based similarity search
- Uses FAISS for efficient vector similarity search

#### LLM Handler (`utils/llm_handler.py`)
- Manages ChatGPT API integration
- Implements advanced prompt engineering techniques
- Provides both demo mode and full API functionality

#### Main Application (`app.py`)
- Streamlit interface with responsive design
- Session state management for conversation history
- Error handling and user feedback

## Configuration

### Environment Variables
Create a `.env` file with:
```env
OPENAI_API_KEY=your-openai-api-key-here
```

### Model Configuration
- **Default Model**: GPT-3.5-turbo (cost-effective)
- **Advanced Model**: GPT-4 (higher quality, higher cost)
- **Demo Mode**: Text-based responses (no API required)

## Testing

### Manual Testing
1. Upload various document types (research papers, reports, manuals)
2. Test with different question types (summary, specific queries, analysis)
3. Verify response quality and relevance
4. Check error handling with invalid files

### Document Types Tested
- ✅ Academic research papers
- ✅ Business reports and financial statements  
- ✅ Technical manuals and documentation
- ✅ Legal contracts and agreements

## Performance Considerations

### Optimization Strategies
- **Chunk Size Optimization**: Configurable chunk sizes for different document types
- **Context Window Management**: Efficient use of model context limits
- **Caching**: Streamlit caching for model loading and embeddings
- **Error Recovery**: Graceful fallbacks for API failures

### Scalability
- **Memory Management**: Efficient handling of large documents
- **Session Management**: Clean session state handling
- **Resource Usage**: Optimized for typical Streamlit deployment

## Security & Privacy

### Data Handling
- **Local Processing**: PDF processing happens locally
- **API Security**: Secure API key management
- **No Data Persistence**: Documents not stored permanently
- **Session Isolation**: Each user session is independent

## Deployment

### Local Development
```bash
streamlit run app.py
```

### Production Deployment
- **Streamlit Community Cloud**: Free hosting option
- **Heroku**: Full-featured deployment
- **Docker**: Containerized deployment option

### Environment Setup
1. Set environment variables in deployment platform
2. Configure secrets management for API keys
3. Set up monitoring and logging

## Future Enhancements

### Planned Features
- [ ] Multi-language document support
- [ ] Document comparison capabilities
- [ ] Export conversation history
- [ ] Advanced filtering and search
- [ ] Integration with document management systems

### Technical Improvements
- [ ] Advanced chunking strategies
- [ ] Custom embedding models
- [ ] Response caching
- [ ] Batch processing capabilities

## Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes with proper documentation
4. Test thoroughly with various document types
5. Submit pull request with clear description

### Code Standards
- **Python Style**: Follow PEP 8 guidelines
- **Documentation**: Comprehensive docstrings for all functions
- **Testing**: Include tests for new features
- **Commits**: Clear, descriptive commit messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **OpenAI**: For ChatGPT API and embedding models
- **Streamlit**: For the excellent web framework
- **PyMuPDF**: For reliable PDF text extraction
- **FAISS**: For efficient vector similarity search

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check existing documentation
- Review code comments for implementation details

---

**Built with ❤️ using Python, Streamlit, and OpenAI**

---

## Docker Support

This project supports containerized deployment using Docker for simplified setup and consistent environments.

### Build the Docker Image

```bash
docker build -t pdf-chatbot .
```

### Run the Application

```bash
docker run -p 8501:8501 --env-file .env pdf-chatbot
```

> Make sure to create a `.env` file in the root directory with your OpenAI API key:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

### Optional: Bind Mount for Local PDFs

If you want to persist files or access local PDFs:

```bash
docker run -p 8501:8501 --env-file .env -v $(pwd)/data:/app/data pdf-chatbot
```

### Clean Up

To stop and remove the container:

```bash
docker ps
docker stop <container_id>
docker rm <container_id>
```
