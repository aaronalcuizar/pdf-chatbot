import numpy as np
import openai
from openai import OpenAI
from typing import List, Dict, Tuple
import streamlit as st
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class EmbeddingsHandler:
    """Handles text embeddings using OpenAI's embedding API"""
    
    def __init__(self):
        """Initialize the embeddings handler"""
        self.client = None
        self.chunks = []
        self.embeddings = []
        self.metadata = []
        self.initialize_client()
        
    def initialize_client(self):
        """Initialize OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings using OpenAI's text-embedding-ada-002 model
        
        Args:
            texts (List[str]): List of text chunks
            
        Returns:
            List[List[float]]: List of embeddings
        """
        if not self.client:
            st.error("OpenAI client not initialized")
            return []
        
        embeddings = []
        
        with st.progress(0) as progress_bar:
            for i, text in enumerate(texts):
                try:
                    # Create embedding using OpenAI API
                    response = self.client.embeddings.create(
                        model="text-embedding-ada-002",
                        input=text.replace("\n", " ")
                    )
                    
                    embedding = response.data[0].embedding
                    embeddings.append(embedding)
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(texts))
                    
                except Exception as e:
                    st.error(f"Error creating embedding for chunk {i}: {str(e)}")
                    # Add a zero vector as fallback
                    embeddings.append([0.0] * 1536)  # ada-002 has 1536 dimensions
        
        return embeddings
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return dot_product / (norm_a * norm_b)
        except:
            return 0.0
    
    def build_vector_index(self, documents: List[Dict]):
        """
        Build vector index from processed documents
        
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
                all_chunks.append(chunk)
                all_metadata.append({
                    'filename': filename,
                    'chunk_id': i,
                    'text': chunk
                })
        
        if not all_chunks:
            st.error("No text chunks found to create embeddings")
            return
        
        st.info(f"Creating embeddings for {len(all_chunks)} chunks...")
        
        # Create embeddings
        embeddings = self.create_embeddings(all_chunks)
        
        if embeddings:
            # Store everything
            self.chunks = all_chunks
            self.embeddings = embeddings
            self.metadata = all_metadata
            
            st.success(f"Vector index built with {len(all_chunks)} chunks from {len(documents)} documents")
        else:
            st.error("Failed to create embeddings")
    
    def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Perform similarity search for a query
        
        Args:
            query (str): Search query
            k (int): Number of top results to return
            
        Returns:
            List[Dict]: List of similar chunks with metadata and scores
        """
        if not self.embeddings:
            st.error("Vector index not built. Please upload and process documents first.")
            return []
        
        if not self.client:
            st.error("OpenAI client not initialized")
            return []
        
        try:
            # Create query embedding
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=query.replace("\n", " ")
            )
            
            query_embedding = response.data[0].embedding
            
            # Calculate similarities
            similarities = []
            for i, chunk_embedding in enumerate(self.embeddings):
                similarity = self.cosine_similarity(query_embedding, chunk_embedding)
                similarities.append((i, similarity))
            
            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Get top k results
            results = []
            for i in range(min(k, len(similarities))):
                idx, score = similarities[i]
                
                if idx < len(self.metadata):
                    result = {
                        'text': self.metadata[idx]['text'],
                        'filename': self.metadata[idx]['filename'],
                        'chunk_id': self.metadata[idx]['chunk_id'],
                        'similarity_score': float(score)
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            st.error(f"Error during similarity search: {str(e)}")
            return []
    
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
            return "No relevant context found in the uploaded documents."
        
        context_parts = []
        for chunk in similar_chunks:
            # Add filename and similarity score for reference
            context_parts.append(
                f"[From {chunk['filename']} - Similarity: {chunk['similarity_score']:.3f}]\n"
                f"{chunk['text']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def get_index_stats(self) -> Dict:
        """
        Get statistics about the current index
        
        Returns:
            Dict: Statistics about the index
        """
        if not self.embeddings:
            return {"status": "No index built"}
        
        unique_docs = len(set(meta['filename'] for meta in self.metadata))
        
        return {
            "status": "Index ready",
            "total_chunks": len(self.chunks),
            "dimension": len(self.embeddings[0]) if self.embeddings else 0,
            "model_name": "text-embedding-ada-002",
            "unique_documents": unique_docs
        }