import re
from typing import List, Dict
import streamlit as st

class EmbeddingsHandler:
    """Simple text-based search handler (no API required)"""
    
    def __init__(self):
        """Initialize the handler"""
        self.chunks = []
        self.metadata = []
        
    def build_vector_index(self, documents: List[Dict]):
        """
        Build simple text index from processed documents
        
        Args:
            documents (List[Dict]): List of processed document dictionaries
        """
        # Collect all chunks and metadata
        all_chunks = []
        all_metadata = []
        
        for doc in documents:
            chunks = doc['chunks']
            filename = doc['filename']
            
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk.lower())  # Convert to lowercase for searching
                all_metadata.append({
                    'filename': filename,
                    'chunk_id': i,
                    'text': chunk,  # Keep original case for display
                    'text_lower': chunk.lower()
                })
        
        if not all_chunks:
            st.error("No text chunks found")
            return
        
        # Store everything
        self.chunks = all_chunks
        self.metadata = all_metadata
        
        st.success(f"Text index built with {len(all_chunks)} chunks from {len(documents)} documents")
    
    def calculate_text_similarity(self, query: str, text: str) -> float:
        """
        Calculate simple text similarity based on keyword overlap
        
        Args:
            query (str): Search query
            text (str): Text to compare against
            
        Returns:
            float: Similarity score (0-1)
        """
        # Convert to lowercase and split into words
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        text_words = set(re.findall(r'\b\w+\b', text.lower()))
        
        if not query_words or not text_words:
            return 0.1  # Give small score instead of 0
        
        # Calculate Jaccard similarity (intersection over union)
        intersection = len(query_words.intersection(text_words))
        union = len(query_words.union(text_words))
        
        jaccard_score = intersection / union if union > 0 else 0.0
        
        # Boost score if query appears as substring
        substring_bonus = 0.3 if query.lower() in text.lower() else 0.0
        
        # Boost score based on how many query words appear
        word_match_ratio = intersection / len(query_words) if query_words else 0.0
        
        # For general questions, give higher base score
        general_questions = ['what', 'about', 'document', 'this', 'content', 'summary', 'main']
        if any(word in query.lower() for word in general_questions):
            base_score = 0.4
        else:
            base_score = 0.0
        
        # Combined score
        final_score = base_score + (jaccard_score * 0.3) + (word_match_ratio * 0.3) + substring_bonus
        
        return min(final_score, 1.0)  # Cap at 1.0
    
    def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Perform text-based similarity search
        
        Args:
            query (str): Search query
            k (int): Number of top results to return
            
        Returns:
            List[Dict]: List of similar chunks with metadata and scores
        """
        if not self.chunks:
            st.error("Text index not built. Please upload and process documents first.")
            return []
        
        # Calculate similarities
        similarities = []
        for i, chunk in enumerate(self.chunks):
            similarity = self.calculate_text_similarity(query, chunk)
            similarities.append((i, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top k results
        results = []
        for i in range(min(k, len(similarities))):
            idx, score = similarities[i]
            
            if idx < len(self.metadata) and score > 0.01:  # More lenient filtering
                result = {
                    'text': self.metadata[idx]['text'],
                    'filename': self.metadata[idx]['filename'],
                    'chunk_id': self.metadata[idx]['chunk_id'],
                    'similarity_score': float(score)
                }
                results.append(result)
        
        return results
    
    def get_context_for_query(self, query: str, max_chunks: int = 3) -> str:
        """
        Get relevant context for a query by combining top similar chunks
        
        Args:
            query (str): User query
            max_chunks (int): Maximum number of chunks to include
            
        Returns:
            str: Combined context text
        """
        similar_chunks = self.similarity_search(query, k=max_chunks)
        
        if not similar_chunks:
            return "No relevant context found in the uploaded documents. The document may not contain information related to your query."
        
        context_parts = []
        for chunk in similar_chunks:
            # Add filename and similarity score for reference
            context_parts.append(
                f"[From {chunk['filename']} - Relevance: {chunk['similarity_score']:.3f}]\n"
                f"{chunk['text']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def get_index_stats(self) -> Dict:
        """
        Get statistics about the current index
        
        Returns:
            Dict: Statistics about the index
        """
        if not self.chunks:
            return {"status": "No index built"}
        
        unique_docs = len(set(meta['filename'] for meta in self.metadata))
        
        return {
            "status": "Index ready",
            "total_chunks": len(self.chunks),
            "dimension": "Text-based search",
            "model_name": "Simple keyword matching",
            "unique_documents": unique_docs
        }