import openai
from openai import OpenAI
import streamlit as st
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import tiktoken

# Load environment variables
load_dotenv()

class LLMHandler:
    """Handles OpenAI API interactions for the PDF chatbot"""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize the LLM handler
        
        Args:
            model (str): OpenAI model to use
        """
        self.model = model
        self.client = None
        self.initialize_client()
        
    def initialize_client(self):
        """Initialize OpenAI client with API key"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("OpenAI API key not found! Please check your .env file.")
            return
        
        try:
            self.client = OpenAI(api_key=api_key)
            # Test the connection with a simple call
            self.client.models.list()
        except Exception as e:
            st.error(f"Error initializing OpenAI client: {str(e)}")
            self.client = None
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken
        
        Args:
            text (str): Text to count tokens for
            
        Returns:
            int: Number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except:
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4
    
    def create_system_prompt(self, context: str) -> str:
        """
        Create system prompt with document context
        
        Args:
            context (str): Relevant document context
            
        Returns:
            str: Formatted system prompt
        """
        return f"""You are a helpful AI assistant that answers questions based on the provided document context.

Instructions:
1. Answer questions using ONLY the information provided in the context below
2. If the answer cannot be found in the context, say "I cannot find this information in the provided documents"
3. Be concise but comprehensive in your responses
4. Quote relevant parts of the document when helpful
5. If the question is unclear, ask for clarification

Document Context:
{context}

Remember: Base your answers strictly on the provided context above."""
    
    def create_financial_prompt(self, context: str) -> str:
        """
        Create specialized prompt for financial document analysis
        
        Args:
            context (str): Financial document context
            
        Returns:
            str: Financial analysis prompt
        """
        return f"""You are a financial analysis AI assistant. Answer questions about financial documents using the provided context.

Specialized Instructions:
1. Focus on financial metrics, ratios, and performance indicators
2. Identify key financial trends and patterns
3. Explain financial terminology when relevant
4. Highlight important financial data like revenue, profit, expenses, assets, liabilities
5. Provide context for financial figures (growth rates, comparisons, etc.)
6. If asked about specific numbers, quote them exactly from the document

Financial Document Context:
{context}

Provide accurate, data-driven financial insights based strictly on the provided context."""
    
    def create_summarization_prompt(self, context: str) -> str:
        """
        Create prompt for document summarization
        
        Args:
            context (str): Document context to summarize
            
        Returns:
            str: Summarization prompt
        """
        return f"""You are a document summarization specialist. Create a comprehensive summary of the provided document content.

Summarization Guidelines:
1. Identify and highlight the main topics and key points
2. Organize information in a logical structure
3. Include important details while maintaining conciseness
4. Use bullet points or numbered lists for clarity
5. Maintain the factual accuracy of the original content
6. Note any significant data, figures, or conclusions

Document Content:
{context}

Create a well-structured summary that captures the essential information from this document."""
    
    def generate_response(self, query: str, context: str, 
                         temperature: float = 0.7, 
                         max_tokens: int = 1000,
                         prompt_type: str = "default") -> Optional[str]:
        """
        Generate response using OpenAI API
        
        Args:
            query (str): User question
            context (str): Relevant document context
            temperature (float): Response creativity (0-1)
            max_tokens (int): Maximum response length
            prompt_type (str): Type of prompt (default, financial, summary)
            
        Returns:
            Optional[str]: Generated response or None if error
        """
        if not self.client:
            st.error("OpenAI client not initialized")
            return None
        
        try:
            # Choose appropriate system prompt
            if prompt_type == "financial":
                system_prompt = self.create_financial_prompt(context)
            elif prompt_type == "summary":
                system_prompt = self.create_summarization_prompt(context)
            else:
                system_prompt = self.create_system_prompt(context)
            
            # Check token count
            total_tokens = self.count_tokens(system_prompt + query)
            if total_tokens > 3500:  # Leave room for response
                st.warning(f"Context is large ({total_tokens} tokens). Response may be truncated.")
            
            # Create chat completion
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            return response.choices[0].message.content
            
        except openai.RateLimitError:
            st.error("OpenAI API rate limit exceeded. Please wait and try again.")
            return None
        except openai.APIError as e:
            st.error(f"OpenAI API error: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None
    
    def generate_follow_up_questions(self, query: str, response: str, context: str) -> List[str]:
        """
        Generate relevant follow-up questions based on the conversation
        
        Args:
            query (str): Original user question
            response (str): AI response
            context (str): Document context
            
        Returns:
            List[str]: List of follow-up questions
        """
        if not self.client:
            return []
        
        try:
            follow_up_prompt = f"""Based on the user's question and the AI response about a document, suggest 3 relevant follow-up questions that would help the user explore the topic further.

User Question: {query}
AI Response: {response}

Generate 3 specific, actionable follow-up questions that:
1. Dig deeper into the topic
2. Explore related aspects mentioned in the document
3. Help clarify or expand understanding

Format as a simple numbered list:
1. [Question 1]
2. [Question 2]
3. [Question 3]"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": follow_up_prompt}],
                temperature=0.8,
                max_tokens=200
            )
            
            # Parse the response to extract questions
            content = response.choices[0].message.content
            questions = []
            
            for line in content.split('\n'):
                line = line.strip()
                if line and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                    question = line[2:].strip()  # Remove number and dot
                    if question:
                        questions.append(question)
            
            return questions[:3]  # Ensure max 3 questions
            
        except Exception as e:
            st.warning(f"Could not generate follow-up questions: {str(e)}")
            return []
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate API cost based on token usage
        
        Args:
            input_tokens (int): Number of input tokens
            output_tokens (int): Number of output tokens
            
        Returns:
            float: Estimated cost in USD
        """
        # Pricing for gpt-3.5-turbo (as of 2024)
        if "gpt-4" in self.model:
            input_cost_per_1k = 0.03
            output_cost_per_1k = 0.06
        else:  # gpt-3.5-turbo
            input_cost_per_1k = 0.0015
            output_cost_per_1k = 0.002
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available OpenAI models
        
        Returns:
            List[str]: List of model names
        """
        if not self.client:
            return ["gpt-3.5-turbo", "gpt-4"]
        
        try:
            models = self.client.models.list()
            chat_models = [model.id for model in models.data 
                          if 'gpt' in model.id and 'turbo' in model.id or 'gpt-4' in model.id]
            return sorted(chat_models)
        except:
            return ["gpt-3.5-turbo", "gpt-4"]
    
    def validate_api_key(self) -> bool:
        """
        Validate if the API key is working
        
        Returns:
            bool: True if API key is valid
        """
        if not self.client:
            return False
        
        try:
            self.client.models.list()
            return True
        except:
            return False 
