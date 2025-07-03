import fitz  # PyMuPDF
import re
from typing import List, Dict
import streamlit as st

class PDFProcessor:
    """Handles PDF text extraction and processing"""
    
    def __init__(self):
        self.documents = []
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """
        Extract text from uploaded PDF file
        
        Args:
            pdf_file: Streamlit uploaded file object
            
        Returns:
            str: Extracted text from PDF
        """
        try:
            # Read PDF bytes
            pdf_bytes = pdf_file.read()
            
            # Open PDF with PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            text = ""
            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
                text += "\n\n"  # Add space between pages
            
            doc.close()
            return text
            
        except Exception as e:
            st.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text (str): Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:\-\(\)\"\'\/]', '', text)
        
        # Remove multiple consecutive periods or dashes
        text = re.sub(r'\.{3,}', '...', text)
        text = re.sub(r'-{3,}', '---', text)
        
        return text.strip()
    
    def split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for better context preservation
        
        Args:
            text (str): Text to split
            chunk_size (int): Maximum characters per chunk
            overlap (int): Number of characters to overlap between chunks
            
        Returns:
            List[str]: List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Find the end position
            end = start + chunk_size
            
            # If we're not at the end of the text, try to break at a sentence
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                last_period = text.rfind('.', end - 100, end)
                last_exclamation = text.rfind('!', end - 100, end)
                last_question = text.rfind('?', end - 100, end)
                
                # Use the latest sentence ending
                sentence_end = max(last_period, last_exclamation, last_question)
                
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def process_pdf(self, pdf_file, chunk_size: int = 1000) -> Dict:
        """
        Complete PDF processing pipeline
        
        Args:
            pdf_file: Streamlit uploaded file object
            chunk_size (int): Size of text chunks
            
        Returns:
            Dict: Processing results with filename, text, and chunks
        """
        with st.spinner(f"Processing {pdf_file.name}..."):
            # Extract text
            raw_text = self.extract_text_from_pdf(pdf_file)
            
            if not raw_text.strip():
                st.warning(f"No text found in {pdf_file.name}")
                return None
            
            # Clean text
            cleaned_text = self.clean_text(raw_text)
            
            # Split into chunks
            chunks = self.split_text_into_chunks(cleaned_text, chunk_size)
            
            # Calculate statistics
            word_count = len(cleaned_text.split())
            char_count = len(cleaned_text)
            
            return {
                'filename': pdf_file.name,
                'text': cleaned_text,
                'chunks': chunks,
                'word_count': word_count,
                'char_count': char_count,
                'chunk_count': len(chunks)
            }
    
    def process_multiple_pdfs(self, pdf_files, chunk_size: int = 1000) -> List[Dict]:
        """
        Process multiple PDF files
        
        Args:
            pdf_files: List of Streamlit uploaded file objects
            chunk_size (int): Size of text chunks
            
        Returns:
            List[Dict]: List of processing results
        """
        results = []
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, pdf_file in enumerate(pdf_files):
            status_text.text(f"Processing {pdf_file.name} ({i+1}/{len(pdf_files)})")
            
            result = self.process_pdf(pdf_file, chunk_size)
            if result:
                results.append(result)
            
            # Update progress
            progress_bar.progress((i + 1) / len(pdf_files))
        
        status_text.text("Processing complete!")
        return results 
