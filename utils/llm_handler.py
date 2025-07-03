import openai
from openai import OpenAI
import streamlit as st
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import tiktoken
import json

load_dotenv()

class LLMHandler:
    """Premium OpenAI handler with multi-turn conversation memory"""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = None
        self.conversation_memory = []  # Store conversation context
        self.max_memory_turns = 5  # Remember last 5 exchanges
        self.initialize_client()
        
    def initialize_client(self):
        """Initialize OpenAI client with API key"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("❌ OpenAI API key not found! Please add OPENAI_API_KEY to your .env file.")
            return
        
        try:
            self.client = OpenAI(api_key=api_key)
            self.client.models.list()
            st.sidebar.success("✅ OpenAI API Connected (Premium Mode)")
        except Exception as e:
            st.sidebar.error(f"❌ OpenAI connection error: {str(e)}")
            self.client = None
    
    def add_to_memory(self, user_message: str, ai_response: str, context_used: str = ""):
        """Add exchange to conversation memory"""
        memory_entry = {
            "user": user_message,
            "assistant": ai_response,
            "context": context_used[:200] + "..." if len(context_used) > 200 else context_used,
            "timestamp": st.session_state.get('current_timestamp', '')
        }
        
        self.conversation_memory.append(memory_entry)
        
        # Keep only recent exchanges
        if len(self.conversation_memory) > self.max_memory_turns:
            self.conversation_memory = self.conversation_memory[-self.max_memory_turns:]
    
    def get_conversation_context(self) -> str:
        """Format conversation memory for context"""
        if not self.conversation_memory:
            return ""
        
        context_parts = ["=== RECENT CONVERSATION HISTORY ==="]
        
        for i, memory in enumerate(self.conversation_memory[-3:], 1):  # Last 3 exchanges
            context_parts.append(f"\nExchange {i}:")
            context_parts.append(f"Human: {memory['user']}")
            context_parts.append(f"Assistant: {memory['assistant'][:150]}...")
            if memory['context']:
                context_parts.append(f"Context used: {memory['context']}")
        
        context_parts.append("\n=== END CONVERSATION HISTORY ===\n")
        return "\n".join(context_parts)
    
    def detect_follow_up_question(self, query: str) -> bool:
        """Detect if current question is a follow-up to previous conversation"""
        follow_up_indicators = [
            "more about", "tell me more", "elaborate", "expand on", "detail",
            "what about", "how about", "also", "additionally", "furthermore",
            "that", "this", "it", "they", "those", "these", "such",
            "why", "how", "when", "where", "continue", "go on"
        ]
        
        query_lower = query.lower()
        
        # Check for pronouns and references that suggest follow-up
        if any(indicator in query_lower for indicator in follow_up_indicators):
            return True
        
        # Check for short questions (likely follow-ups)
        if len(query.split()) <= 5 and self.conversation_memory:
            return True
        
        return False
    
    def create_context_aware_prompt(self, query: str, context: str, doc_type: str) -> str:
        """Create context-aware prompt that includes conversation memory"""
        
        # Base instructions with conversation awareness
        base_instructions = """You are an expert document analyst with perfect conversation memory. You can reference and build upon our previous discussion.

CONVERSATION AWARENESS INSTRUCTIONS:
1. Remember our previous exchanges and refer to them when relevant
2. Build upon earlier answers to provide deeper insights  
3. Connect current questions to previous topics we've discussed
4. Use phrases like "As we discussed earlier..." or "Building on my previous response..."
5. Maintain consistency with all previous statements

CORE ANALYSIS INSTRUCTIONS:
1. Answer based on the provided document content and our conversation history
2. Be thorough, accurate, and provide specific details
3. Use clear formatting with headers and bullet points
4. Quote relevant sections when helpful
5. If information isn't in the document, clearly state that
6. Provide actionable insights when appropriate"""

        # Get conversation context
        conversation_context = self.get_conversation_context()
        
        # Check if this is a follow-up question
        is_follow_up = self.detect_follow_up_question(query)
        
        if is_follow_up and conversation_context:
            follow_up_instruction = """
FOLLOW-UP QUESTION DETECTED:
This appears to be a follow-up to our previous conversation. Please:
- Reference relevant parts of our previous discussion
- Build upon earlier answers
- Provide deeper analysis or additional details
- Connect this question to previous topics"""
        else:
            follow_up_instruction = ""

        specialized_prompts = {
            "research_paper": f"""{base_instructions}

Document Type: Academic Research Paper
{follow_up_instruction}

{conversation_context}

Current Document Context:
{context}""",

            "business_report": f"""{base_instructions}

Document Type: Business/Financial Report
{follow_up_instruction}

Specialized Focus:
- Build upon any financial metrics we've previously discussed
- Reference earlier business strategy points when relevant
- Provide comparative analysis with previous insights

{conversation_context}

Current Document Context:
{context}""",

            "general_document": f"""{base_instructions}

Document Type: General Document
{follow_up_instruction}

{conversation_context}

Current Document Context:
{context}"""
        }
        
        return specialized_prompts.get(doc_type, specialized_prompts["general_document"])
    
    def generate_response(self, query: str, context: str, 
                         temperature: float = 0.7, 
                         max_tokens: int = 1500,
                         prompt_type: str = "default") -> Optional[str]:
        """Generate response with conversation memory"""
        if not self.client:
            return """**⚠️ OpenAI API Not Available**

To get intelligent responses, please:
1. Add your OpenAI API key to the `.env` file
2. Ensure you have credits in your OpenAI account
3. Restart the application"""
        
        if not context or "No relevant context found" in context:
            return """**📄 No Document Content Available**

Please upload a PDF document first to enable intelligent Q&A functionality."""
        
        try:
            # Detect document type for specialized prompting
            doc_type = self.detect_document_type(context)
            
            # Create context-aware system prompt
            system_prompt = self.create_context_aware_prompt(query, context, doc_type)
            
            # Add conversation awareness to user message
            if self.detect_follow_up_question(query) and self.conversation_memory:
                enhanced_query = f"""Current question: {query}

Note: This appears to be a follow-up question. Please reference our previous conversation when relevant and build upon earlier insights."""
            else:
                enhanced_query = query
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": enhanced_query}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            generated_response = response.choices[0].message.content
            
            # Add to conversation memory
            self.add_to_memory(query, generated_response, context)
            
            # Add metadata
            usage = response.usage
            response_metadata = f"\n\n---\n*📊 Response generated using {self.model} • Tokens used: {usage.total_tokens} • Cost: ~${self.estimate_cost(usage.prompt_tokens, usage.completion_tokens):.4f}*"
            
            # Add conversation memory indicator
            if self.conversation_memory:
                memory_indicator = f" • 🧠 Memory: {len(self.conversation_memory)} exchanges"
                response_metadata += memory_indicator
            
            return generated_response + response_metadata
            
        except Exception as e:
            return f"**⚠️ Error generating response:** {str(e)}"
    
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
    
    def get_memory_stats(self) -> Dict:
        """Get conversation memory statistics"""
        return {
            "total_exchanges": len(self.conversation_memory),
            "memory_limit": self.max_memory_turns,
            "last_exchange": self.conversation_memory[-1]['timestamp'] if self.conversation_memory else "None",
            "conversation_started": len(self.conversation_memory) > 0
        }
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.conversation_memory = []
    
    def export_memory(self) -> str:
        """Export conversation memory as JSON"""
        return json.dumps(self.conversation_memory, indent=2)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except:
            return len(text.split()) * 1.3
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate API cost based on current OpenAI pricing"""
        if "gpt-4" in self.model:
            input_cost_per_1k = 0.03
            output_cost_per_1k = 0.06
        else:
            input_cost_per_1k = 0.0015
            output_cost_per_1k = 0.002
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost