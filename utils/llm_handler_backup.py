import openai
from openai import OpenAI
import streamlit as st
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import tiktoken
import json

# Load environment variables
load_dotenv()

class LLMHandler:
    """Premium OpenAI handler with full ChatGPT integration"""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize the premium LLM handler
        
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
            st.error("❌ OpenAI API key not found! Please add OPENAI_API_KEY to your .env file.")
            return
        
        try:
            self.client = OpenAI(api_key=api_key)
            # Test the connection
            self.client.models.list()
            st.sidebar.success("✅ OpenAI API Connected (Premium Mode)")
        except openai.AuthenticationError:
            st.sidebar.error("❌ Invalid OpenAI API key. Please check your .env file.")
            self.client = None
        except openai.RateLimitError:
            st.sidebar.warning("⚠️ OpenAI rate limit. You may need to add credits to your account.")
            self.client = None
        except Exception as e:
            st.sidebar.error(f"❌ OpenAI connection error: {str(e)}")
            self.client = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except:
            # Fallback estimation
            return len(text.split()) * 1.3
    
    def detect_document_type(self, context: str) -> str:
        """Detect document type for specialized prompting"""
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['research', 'study', 'methodology', 'hypothesis', 'abstract']):
            return "research_paper"
        elif any(word in context_lower for word in ['revenue', 'profit', 'financial', 'quarterly', 'annual', 'earnings']):
            return "business_report"
        elif any(word in context_lower for word in ['contract', 'agreement', 'terms', 'legal', 'clause']):
            return "legal_document"
        elif any(word in context_lower for word in ['manual', 'guide', 'instructions', 'procedure']):
            return "technical_manual"
        else:
            return "general_document"
    
    def create_specialized_prompt(self, context: str, doc_type: str) -> str:
        """Create specialized system prompts based on document type"""
        
        base_instructions = """You are an expert document analyst. Analyze the provided document content and answer questions with high accuracy and insight.

Core Instructions:
1. Answer based ONLY on the provided document content
2. Be thorough, accurate, and provide specific details
3. Use clear formatting with headers and bullet points
4. Quote relevant sections when helpful
5. If information isn't in the document, clearly state that
6. Provide actionable insights when appropriate"""

        specialized_prompts = {
            "research_paper": f"""{base_instructions}

Document Type: Academic Research Paper
Specialized Focus:
- Identify research objectives, hypotheses, and methodology
- Highlight key findings, results, and statistical significance
- Explain research implications and limitations
- Summarize conclusions and future research directions
- Extract quantitative data and experimental details

Document Content:
{context}""",

            "business_report": f"""{base_instructions}

Document Type: Business/Financial Report  
Specialized Focus:
- Extract key financial metrics (revenue, profit, growth rates)
- Identify strategic initiatives and business objectives
- Analyze market trends and competitive positioning
- Highlight performance indicators and benchmarks
- Summarize executive decisions and future outlook

Document Content:
{context}""",

            "legal_document": f"""{base_instructions}

Document Type: Legal Document
Specialized Focus:
- Identify key terms, conditions, and obligations
- Highlight important clauses and legal requirements
- Extract dates, deadlines, and compliance requirements
- Explain rights, responsibilities, and limitations
- Summarize legal implications and consequences

Document Content:
{context}""",

            "technical_manual": f"""{base_instructions}

Document Type: Technical Manual/Guide
Specialized Focus:
- Extract step-by-step procedures and instructions
- Identify system requirements and specifications
- Highlight safety warnings and precautions
- Explain features, capabilities, and limitations
- Provide troubleshooting guidance when available

Document Content:
{context}""",

            "general_document": f"""{base_instructions}

Document Type: General Document
Specialized Focus:
- Identify main topics and key themes
- Extract important facts and data points
- Summarize key arguments and conclusions
- Highlight actionable information
- Provide comprehensive overview of content

Document Content:
{context}"""
        }
        
        return specialized_prompts.get(doc_type, specialized_prompts["general_document"])
    
    def generate_response(self, query: str, context: str, 
                         temperature: float = 0.7, 
                         max_tokens: int = 1500,
                         prompt_type: str = "default") -> Optional[str]:
        """
        Generate premium response using OpenAI ChatGPT
        
        Args:
            query (str): User question
            context (str): Document context
            temperature (float): Response creativity
            max_tokens (int): Maximum response length
            prompt_type (str): Type of prompt
            
        Returns:
            Optional[str]: Generated response
        """
        if not self.client:
            return """**⚠️ OpenAI API Not Available**

To get intelligent responses, please:
1. Add your OpenAI API key to the `.env` file
2. Ensure you have credits in your OpenAI account
3. Restart the application

**Current Mode**: Demo mode with limited functionality."""
        
        if not context or "No relevant context found" in context:
            return """**📄 No Document Content Available**

Please upload a PDF document first to enable intelligent Q&A functionality.

**What I can do once you upload a document:**
• **Detailed Analysis**: Comprehensive document analysis
• **Specific Q&A**: Answer precise questions about content  
• **Smart Summaries**: Create executive summaries
• **Data Extraction**: Extract key metrics and information
• **Context-Aware Responses**: Adapt to document type automatically

Upload any PDF to get started!"""
        
        try:
            # Detect document type for specialized prompting
            doc_type = self.detect_document_type(context)
            
            # Create specialized system prompt
            system_prompt = self.create_specialized_prompt(context, doc_type)
            
            # Check token count and truncate if necessary
            system_tokens = self.count_tokens(system_prompt)
            query_tokens = self.count_tokens(query)
            available_tokens = 4000 - max_tokens - query_tokens  # Leave room for response
            
            if system_tokens > available_tokens:
                # Truncate context while preserving structure
                context_lines = context.split('\n')
                truncated_context = []
                current_tokens = 0
                
                for line in context_lines:
                    line_tokens = self.count_tokens(line)
                    if current_tokens + line_tokens < available_tokens * 0.8:  # Use 80% of available
                        truncated_context.append(line)
                        current_tokens += line_tokens
                    else:
                        truncated_context.append("... [Content truncated for length] ...")
                        break
                
                context = '\n'.join(truncated_context)
                system_prompt = self.create_specialized_prompt(context, doc_type)
            
            # Generate response with ChatGPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            generated_response = response.choices[0].message.content
            
            # Add metadata about the response
            usage = response.usage
            response_metadata = f"\n\n---\n*📊 Response generated using {self.model} • Tokens used: {usage.total_tokens} • Cost: ~${self.estimate_cost(usage.prompt_tokens, usage.completion_tokens):.4f}*"
            
            return generated_response + response_metadata
            
        except openai.RateLimitError:
            return """**⚠️ OpenAI Rate Limit Exceeded**

You've reached the rate limit for your OpenAI account. Please:
1. Wait a few minutes and try again
2. Check your usage at: https://platform.openai.com/account/usage
3. Consider upgrading your plan for higher limits

The rate limit typically resets within 1 minute."""

        except openai.APIError as e:
            return f"""**⚠️ OpenAI API Error**

Error: {str(e)}

**Possible solutions:**
1. Check your internet connection
2. Verify your API key is valid
3. Ensure you have sufficient credits
4. Try again in a few moments"""

        except Exception as e:
            return f"""**⚠️ Unexpected Error**

An error occurred while generating the response: {str(e)}

**Please try:**
1. Asking a simpler question
2. Rephrasing your query
3. Checking your internet connection"""
    
    def generate_summary(self, context: str) -> str:
        """Generate comprehensive document summary"""
        if not self.client:
            return "OpenAI API not available for summary generation."
        
        summary_query = "Please provide a comprehensive, well-structured summary of this document. Include the main topics, key findings, important data, and conclusions."
        
        return self.generate_response(
            query=summary_query,
            context=context,
            temperature=0.3,  # Lower temperature for more focused summaries
            max_tokens=2000,
            prompt_type="summary"
        )
    
    def generate_follow_up_questions(self, query: str, response: str, context: str) -> List[str]:
        """Generate intelligent follow-up questions"""
        if not self.client:
            return [
                "What are the main topics in this document?",
                "Can you provide more specific details?",
                "What are the key conclusions?"
            ]
        
        try:
            doc_type = self.detect_document_type(context)
            
            follow_up_prompt = f"""Based on this conversation about a {doc_type}, suggest 3 highly relevant follow-up questions that would provide deeper insights.

User Question: {query}
AI Response Summary: {response[:200]}...

Generate 3 specific, insightful questions that:
1. Explore deeper aspects of the topic
2. Uncover additional relevant information
3. Help the user gain more comprehensive understanding

Format as:
1. [Question focusing on details/specifics]
2. [Question exploring implications/context]  
3. [Question about related aspects/next steps]"""

            follow_up_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": follow_up_prompt}],
                temperature=0.8,
                max_tokens=300
            )
            
            content = follow_up_response.choices[0].message.content
            questions = []
            
            for line in content.split('\n'):
                line = line.strip()
                if line and any(line.startswith(f'{i}.') for i in range(1, 4)):
                    question = re.sub(r'^\d+\.\s*', '', line).strip()
                    if question and len(question) > 10:
                        questions.append(question)
            
            return questions[:3]
            
        except Exception as e:
            # Fallback questions based on document type
            fallback_questions = {
                "research_paper": [
                    "What methodology was used in this research?",
                    "What are the key limitations of this study?",
                    "How do these findings compare to previous research?"
                ],
                "business_report": [
                    "What are the main growth drivers mentioned?",
                    "How does performance compare to industry benchmarks?",
                    "What strategic initiatives are planned?"
                ],
                "legal_document": [
                    "What are the key obligations for each party?",
                    "What are the termination conditions?",
                    "What compliance requirements are specified?"
                ]
            }
            
            doc_type = self.detect_document_type(context)
            return fallback_questions.get(doc_type, [
                "What additional details can you provide?",
                "What are the implications of these findings?",
                "How does this relate to the broader context?"
            ])
    
    def validate_api_key(self) -> bool:
        """Validate OpenAI API key and connection"""
        return self.client is not None
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models"""
        if not self.client:
            return ["gpt-3.5-turbo", "gpt-4"]
        
        try:
            models = self.client.models.list()
            chat_models = [
                model.id for model in models.data 
                if any(name in model.id for name in ['gpt-3.5', 'gpt-4'])
            ]
            return sorted(chat_models) if chat_models else ["gpt-3.5-turbo", "gpt-4"]
        except:
            return ["gpt-3.5-turbo", "gpt-4"]
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate API cost based on current OpenAI pricing"""
        # GPT-3.5-turbo pricing (as of 2024)
        if "gpt-4" in self.model:
            input_cost_per_1k = 0.03   # $30 per 1M tokens
            output_cost_per_1k = 0.06  # $60 per 1M tokens  
        else:  # gpt-3.5-turbo
            input_cost_per_1k = 0.0015  # $1.50 per 1M tokens
            output_cost_per_1k = 0.002  # $2.00 per 1M tokens
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        if not self.client:
            return {"status": "API not connected"}
        
        try:
            # Note: OpenAI doesn't provide real-time usage via API
            # This would need to be tracked internally
            return {
                "status": "Connected",
                "model": self.model,
                "estimated_cost_per_query": "$0.001-0.01",
                "recommendation": "Monitor usage at platform.openai.com"
            }
        except:
            return {"status": "Unable to retrieve usage data"}