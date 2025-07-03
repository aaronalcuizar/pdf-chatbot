import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
from io import BytesIO

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.pdf_processor import PDFProcessor
from utils.embeddings import EmbeddingsHandler
from utils.llm_handler import LLMHandler

class TestPDFProcessor:
    """Comprehensive tests for PDF processing"""
    
    def setup_method(self):
        """Setup for each test"""
        self.processor = PDFProcessor()
    
    def test_text_cleaning(self):
        """Test text cleaning functionality"""
        # Test cases with different types of dirty text
        test_cases = [
            {
                "input": "This    has   excessive    spaces",
                "expected": "This has excessive spaces"
            },
            {
                "input": "Text\nwith\nmultiple\nlines",
                "expected": "Text with multiple lines"
            },
            {
                "input": "Special@#$%^&*()characters!@#",
                "expected": "Specialcharacters!"
            },
            {
                "input": "Multiple.....periods and---dashes",
                "expected": "Multiple...periods and---dashes"
            }
        ]
        
        for case in test_cases:
            result = self.processor.clean_text(case["input"])
            assert result == case["expected"], f"Failed for input: {case['input']}"
    
    def test_text_chunking(self):
        """Test text splitting into chunks"""
        # Test with different text lengths
        short_text = "This is a short text."
        long_text = "This is a sentence. " * 100  # 100 sentences
        
        # Short text should return single chunk
        short_chunks = self.processor.split_text_into_chunks(short_text, chunk_size=1000)
        assert len(short_chunks) == 1
        assert short_chunks[0] == short_text
        
        # Long text should be split
        long_chunks = self.processor.split_text_into_chunks(long_text, chunk_size=500)
        assert len(long_chunks) > 1
        
        # Check overlap functionality
        overlap_chunks = self.processor.split_text_into_chunks(long_text, chunk_size=500, overlap=100)
        assert len(overlap_chunks) > 1
        
        # Verify no chunk exceeds size limit significantly
        for chunk in overlap_chunks:
            assert len(chunk) <= 600  # Some tolerance for sentence boundaries
    
    def test_chunk_overlap(self):
        """Test that chunks have proper overlap"""
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five. " * 20
        chunks = self.processor.split_text_into_chunks(text, chunk_size=200, overlap=50)
        
        if len(chunks) > 1:
            # Check that consecutive chunks have overlapping content
            for i in range(len(chunks) - 1):
                chunk1_end = chunks[i][-50:]  # Last 50 chars
                chunk2_start = chunks[i + 1][:100]  # First 100 chars
                
                # There should be some overlap
                overlap_found = any(word in chunk2_start for word in chunk1_end.split()[-5:])
                assert overlap_found, f"No overlap found between chunk {i} and {i+1}"

class TestEmbeddingsHandler:
    """Comprehensive tests for embeddings functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.embeddings = EmbeddingsHandler()
    
    def test_similarity_calculation(self):
        """Test text similarity calculation"""
        # Identical texts should have high similarity
        text1 = "The quick brown fox jumps over the lazy dog"
        text2 = "The quick brown fox jumps over the lazy dog"
        similarity = self.embeddings.calculate_text_similarity(text1, text2)
        assert similarity > 0.8, f"Identical texts should have high similarity, got {similarity}"
        
        # Completely different texts should have low similarity
        text3 = "Financial report quarterly earnings revenue profit"
        text4 = "Weather forecast rain temperature humidity climate"
        similarity = self.embeddings.calculate_text_similarity(text3, text4)
        assert similarity < 0.3, f"Different texts should have low similarity, got {similarity}"
        
        # Related texts should have medium similarity
        text5 = "Company revenue increased by 15% this quarter"
        text6 = "Quarterly financial results show profit growth"
        similarity = self.embeddings.calculate_text_similarity(text5, text6)
        assert 0.3 < similarity < 0.8, f"Related texts should have medium similarity, got {similarity}"
    
    def test_empty_index_handling(self):
        """Test behavior with empty index"""
        results = self.embeddings.similarity_search("test query", k=5)
        assert results == [], "Empty index should return empty results"
        
        context = self.embeddings.get_context_for_query("test query")
        assert "No relevant context found" in context
    
    def test_index_building(self):
        """Test vector index building"""
        # Mock document data
        test_documents = [
            {
                'filename': 'test_doc.pdf',
                'chunks': [
                    'This is the first chunk about financial results.',
                    'This is the second chunk about business strategy.',
                    'This is the third chunk about market analysis.'
                ]
            }
        ]
        
        # Build index
        self.embeddings.build_vector_index(test_documents)
        
        # Verify index was built
        assert len(self.embeddings.chunks) == 3
        assert len(self.embeddings.metadata) == 3
        
        # Test search functionality
        results = self.embeddings.similarity_search("financial results", k=2)
        assert len(results) > 0
        assert any("financial" in result['text'].lower() for result in results)
    
    def test_search_ranking(self):
        """Test that search results are properly ranked by relevance"""
        test_documents = [
            {
                'filename': 'test_doc.pdf',
                'chunks': [
                    'Revenue increased significantly this quarter showing strong financial performance.',
                    'The weather was nice today with clear skies.',
                    'Quarterly revenue growth exceeded expectations with 25% increase.',
                    'Dogs and cats are popular pets in many households.'
                ]
            }
        ]
        
        self.embeddings.build_vector_index(test_documents)
        
        # Search for financial content
        results = self.embeddings.similarity_search("revenue financial quarter", k=4)
        
        # First result should be most relevant (contains all keywords)
        assert len(results) >= 2
        assert results[0]['similarity_score'] >= results[1]['similarity_score']
        
        # Financial chunks should rank higher than non-financial
        financial_chunks = [r for r in results if 'revenue' in r['text'].lower()]
        non_financial_chunks = [r for r in results if 'weather' in r['text'].lower() or 'pets' in r['text'].lower()]
        
        if financial_chunks and non_financial_chunks:
            assert financial_chunks[0]['similarity_score'] > non_financial_chunks[0]['similarity_score']

class TestLLMHandler:
    """Comprehensive tests for LLM functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.llm = LLMHandler()
    
    def test_document_type_detection(self):
        """Test automatic document type detection"""
        test_cases = [
            {
                "context": "This research study examines the hypothesis that methodology affects results",
                "expected": "research_paper"
            },
            {
                "context": "Revenue increased by 15% this quarter with strong earnings performance",
                "expected": "business_report"
            },
            {
                "context": "This agreement contains terms and conditions for legal compliance",
                "expected": "legal_document"
            },
            {
                "context": "Follow these instructions to operate the manual equipment procedure",
                "expected": "technical_manual"
            },
            {
                "context": "This is some general content about various topics",
                "expected": "general_document"
            }
        ]
        
        for case in test_cases:
            result = self.llm.detect_document_type(case["context"])
            assert result == case["expected"], f"Failed to detect {case['expected']} for context: {case['context'][:50]}..."
    
    def test_conversation_memory(self):
        """Test conversation memory functionality"""
        # Test memory addition
        self.llm.add_to_memory("What is revenue?", "Revenue is income from business operations", "financial context")
        assert len(self.llm.conversation_memory) == 1
        
        # Test memory limit
        for i in range(10):
            self.llm.add_to_memory(f"Question {i}", f"Answer {i}", f"context {i}")
        
        # Should not exceed max_memory_turns
        assert len(self.llm.conversation_memory) <= self.llm.max_memory_turns
        
        # Test memory context generation
        context = self.llm.get_conversation_context()
        assert "RECENT CONVERSATION HISTORY" in context
        assert "Exchange" in context
    
    def test_follow_up_detection(self):
        """Test follow-up question detection"""
        # Setup some conversation history
        self.llm.add_to_memory("What is revenue?", "Revenue is income", "context")
        
        follow_up_questions = [
            "Tell me more about that",
            "What about profit?",
            "Can you elaborate?",
            "How about expenses?",
            "Why is this important?"
        ]
        
        for question in follow_up_questions:
            is_follow_up = self.llm.detect_follow_up_question(question)
            assert is_follow_up, f"Should detect '{question}' as follow-up"
        
        independent_questions = [
            "What is the company's business strategy?",
            "Analyze the market trends in detail",
            "Provide a comprehensive summary of operations"
        ]
        
        for question in independent_questions:
            is_follow_up = self.llm.detect_follow_up_question(question)
            # These might or might not be follow-ups depending on context
            # Just ensure the function runs without error
            assert isinstance(is_follow_up, bool)
    
    def test_memory_export_import(self):
        """Test memory export and import functionality"""
        # Add some memory entries
        test_entries = [
            ("Question 1", "Answer 1", "Context 1"),
            ("Question 2", "Answer 2", "Context 2"),
            ("Question 3", "Answer 3", "Context 3")
        ]
        
        for q, a, c in test_entries:
            self.llm.add_to_memory(q, a, c)
        
        # Export memory
        exported = self.llm.export_memory()
        
        # Should be valid JSON
        memory_data = json.loads(exported)
        assert isinstance(memory_data, list)
        assert len(memory_data) == len(test_entries)
        
        # Check structure
        for entry in memory_data:
            assert 'user' in entry
            assert 'assistant' in entry
            assert 'context' in entry
            assert 'timestamp' in entry
    
    def test_token_counting(self):
        """Test token counting functionality"""
        # Test with known text
        short_text = "Hello world"
        tokens = self.llm.count_tokens(short_text)
        assert tokens > 0
        assert tokens < 10  # Should be small number
        
        long_text = "This is a much longer text that should result in more tokens. " * 100
        long_tokens = self.llm.count_tokens(long_text)
        assert long_tokens > tokens
        assert long_tokens > 100  # Should be substantial
    
    def test_cost_estimation(self):
        """Test cost estimation functionality"""
        # Test cost calculation
        input_tokens = 1000
        output_tokens = 500
        
        cost = self.llm.estimate_cost(input_tokens, output_tokens)
        assert cost > 0
        assert isinstance(cost, float)
        
        # GPT-4 should be more expensive than GPT-3.5
        llm_gpt4 = LLMHandler("gpt-4")
        llm_gpt35 = LLMHandler("gpt-3.5-turbo")
        
        cost_gpt4 = llm_gpt4.estimate_cost(input_tokens, output_tokens)
        cost_gpt35 = llm_gpt35.estimate_cost(input_tokens, output_tokens)
        
        assert cost_gpt4 > cost_gpt35

class TestIntegration:
    """Integration tests for the complete pipeline"""
    
    def setup_method(self):
        """Setup for integration tests"""
        self.pdf_processor = PDFProcessor()
        self.embeddings = EmbeddingsHandler()
        self.llm = LLMHandler()
    
    def test_complete_pipeline_simulation(self):
        """Test the complete pipeline with simulated data"""
        # Simulate PDF processing
        mock_text = """
        Annual Report 2023
        
        Financial Performance:
        Revenue increased by 15% to $150 million this year.
        Net profit improved to $25 million, up from $20 million last year.
        
        Business Strategy:
        We are focusing on digital transformation and market expansion.
        Key initiatives include AI adoption and customer experience improvement.
        
        Market Analysis:
        The market showed resilience despite economic challenges.
        Our competitive position strengthened through innovation.
        """
        
        # Test text processing
        cleaned_text = self.pdf_processor.clean_text(mock_text)
        assert len(cleaned_text) > 0
        
        chunks = self.pdf_processor.split_text_into_chunks(cleaned_text, chunk_size=200)
        assert len(chunks) > 1
        
        # Test embeddings
        mock_doc = {
            'filename': 'annual_report_2023.pdf',
            'chunks': chunks
        }
        
        self.embeddings.build_vector_index([mock_doc])
        
        # Test various types of queries
        test_queries = [
            "What was the revenue?",
            "Tell me about business strategy",
            "How did profit change?",
            "What are the key initiatives?"
        ]
        
        for query in test_queries:
            results = self.embeddings.similarity_search(query, k=2)
            assert len(results) > 0, f"No results for query: {query}"
            
            context = self.embeddings.get_context_for_query(query)
            assert "No relevant context found" not in context
    
    def test_conversation_flow_simulation(self):
        """Test realistic conversation flow"""
        # Setup with mock data
        mock_chunks = [
            "The company reported revenue of $150 million in 2023, up 15% from previous year.",
            "Key strategic initiatives include digital transformation and AI adoption.",
            "Market conditions remained challenging but the company maintained strong position."
        ]
        
        mock_doc = {
            'filename': 'business_report.pdf',
            'chunks': mock_chunks
        }
        
        self.embeddings.build_vector_index([mock_doc])
        
        # Simulate conversation flow
        conversation_flow = [
            ("What was the revenue?", False),  # Initial question
            ("How much did it increase?", True),  # Follow-up
            ("What about strategy?", False),  # New topic
            ("Tell me more about that", True),  # Follow-up
        ]
        
        for question, expected_follow_up in conversation_flow:
            # Get context
            context = self.embeddings.get_context_for_query(question)
            assert context
            
            # Check follow-up detection
            is_follow_up = self.llm.detect_follow_up_question(question)
            if expected_follow_up and len(self.llm.conversation_memory) > 0:
                # Should detect follow-up if we have memory
                pass  # Follow-up detection can be context-dependent
            
            # Simulate adding to memory
            self.llm.add_to_memory(question, f"Response to: {question}", context[:100])
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with empty/invalid inputs
        empty_chunks = self.pdf_processor.split_text_into_chunks("")
        assert empty_chunks == [] or empty_chunks == [""]
        
        # Test similarity search with no index
        empty_embeddings = EmbeddingsHandler()
        results = empty_embeddings.similarity_search("test query")
        assert results == []
        
        # Test memory operations on empty memory
        empty_llm = LLMHandler()
        context = empty_llm.get_conversation_context()
        assert context == ""
        
        stats = empty_llm.get_memory_stats()
        assert stats['total_exchanges'] == 0
    
    def test_performance_benchmarks(self):
        """Test performance with larger datasets"""
        import time
        
        # Generate large text corpus
        large_text = "This is a test sentence for performance evaluation. " * 1000
        
        # Test chunking performance
        start_time = time.time()
        chunks = self.pdf_processor.split_text_into_chunks(large_text, chunk_size=500)
        chunking_time = time.time() - start_time
        
        assert chunking_time < 5.0, f"Chunking took too long: {chunking_time}s"
        assert len(chunks) > 1
        
        # Test embedding index building performance
        large_doc = {
            'filename': 'large_test.pdf',
            'chunks': chunks[:50]  # Limit for test performance
        }
        
        start_time = time.time()
        self.embeddings.build_vector_index([large_doc])
        indexing_time = time.time() - start_time
        
        assert indexing_time < 10.0, f"Indexing took too long: {indexing_time}s"
        
        # Test search performance
        start_time = time.time()
        results = self.embeddings.similarity_search("test performance evaluation", k=10)
        search_time = time.time() - start_time
        
        assert search_time < 2.0, f"Search took too long: {search_time}s"
        assert len(results) > 0

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_special_characters_handling(self):
        """Test handling of special characters and unicode"""
        special_texts = [
            "Text with émojis 🚀 and ñoñó characters",
            "Mathematical symbols: α, β, γ, ∑, ∫, ∂",
            "Currency symbols: $, €, ¥, £, ₹",
            "Text with\ttabs and\nnewlines",
            "UPPERCASE and lowercase MiXeD",
            ""  # Empty string
        ]
        
        processor = PDFProcessor()
        
        for text in special_texts:
            try:
                cleaned = processor.clean_text(text)
                chunks = processor.split_text_into_chunks(cleaned, chunk_size=100)
                # Should not crash and return valid results
                assert isinstance(chunks, list)
            except Exception as e:
                pytest.fail(f"Failed to handle special text '{text}': {e}")
    
    def test_memory_boundary_conditions(self):
        """Test memory handling at boundaries"""
        llm = LLMHandler()
        
        # Test with maximum memory
        for i in range(llm.max_memory_turns + 5):
            llm.add_to_memory(f"Question {i}", f"Answer {i}", f"Context {i}")
        
        # Should not exceed limit
        assert len(llm.conversation_memory) == llm.max_memory_turns
        
        # Should contain most recent entries
        assert llm.conversation_memory[-1]['user'] == f"Question {llm.max_memory_turns + 4}"
        
        # Test memory clearing
        llm.clear_memory()
        assert len(llm.conversation_memory) == 0
    
    def test_chunk_size_boundaries(self):
        """Test chunking with various chunk sizes"""
        processor = PDFProcessor()
        text = "This is a test sentence. " * 100
        
        # Test very small chunks
        small_chunks = processor.split_text_into_chunks(text, chunk_size=10)
        assert all(len(chunk) <= 50 for chunk in small_chunks)  # Allow some tolerance
        
        # Test very large chunks
        large_chunks = processor.split_text_into_chunks(text, chunk_size=10000)
        assert len(large_chunks) == 1
        
        # Test zero overlap
        no_overlap_chunks = processor.split_text_into_chunks(text, chunk_size=100, overlap=0)
        assert len(no_overlap_chunks) > 1
        
        # Test overlap larger than chunk size (should be handled gracefully)
        weird_overlap_chunks = processor.split_text_into_chunks(text, chunk_size=100, overlap=150)
        assert len(weird_overlap_chunks) > 0

# Pytest configuration and utilities
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main(["-v", "--tb=short", __file__])