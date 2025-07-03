import streamlit as st
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import re
import random

# Load environment variables
load_dotenv()

class LLMHandler:
    """Complete smart demo LLM handler with dynamic content analysis for all document types"""
    
    def __init__(self, model: str = "smart-dynamic-demo"):
        """
        Initialize the smart dynamic LLM handler
        
        Args:
            model (str): Model name (smart dynamic demo mode)
        """
        self.model = model
        self.api_available = False
        
        # Check if API key exists
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            st.info("🔄 Smart Dynamic Demo: Intelligent responses that adapt to any document type")
        else:
            st.info("🆓 Smart Dynamic Demo: No API key required - works with all PDF types")
    
    def extract_key_information(self, context: str) -> Dict[str, str]:
        """Enhanced extraction that adapts to all document types"""
        context_lower = context.lower()
        
        # Advanced document type detection
        doc_type = "Document"
        field = "General"
        
        # Research papers
        if any(word in context_lower for word in ['research', 'study', 'manuscript', 'paper', 'thesis', 'dissertation', 'journal']):
            doc_type = "Research Paper"
            if any(word in context_lower for word in ['computer', 'engineering', 'algorithm', 'cnn', 'opencv', 'software', 'programming']):
                field = "Computer Engineering"
            elif any(word in context_lower for word in ['medical', 'health', 'clinical', 'patient', 'medicine', 'healthcare']):
                field = "Medical Research"
            elif any(word in context_lower for word in ['business', 'management', 'finance', 'economic', 'marketing', 'strategy']):
                field = "Business Research"
            elif any(word in context_lower for word in ['psychology', 'behavior', 'social', 'cognitive', 'mental']):
                field = "Psychology/Social Science"
            elif any(word in context_lower for word in ['education', 'learning', 'teaching', 'pedagogy', 'curriculum']):
                field = "Educational Research"
            else:
                field = "Academic Research"
        
        # Business documents
        elif any(word in context_lower for word in ['report', 'quarterly', 'annual', 'financial', 'revenue', 'profit', 'budget', 'forecast']):
            doc_type = "Business Report"
            field = "Business/Finance"
        
        # Technical documents
        elif any(word in context_lower for word in ['manual', 'guide', 'instruction', 'procedure', 'specification', 'documentation']):
            doc_type = "Technical Manual"
            field = "Technical Documentation"
        
        # Legal documents
        elif any(word in context_lower for word in ['contract', 'agreement', 'legal', 'terms', 'conditions', 'clause', 'liability']):
            doc_type = "Legal Document"
            field = "Legal"
        
        # Academic documents
        elif any(word in context_lower for word in ['curriculum', 'syllabus', 'course', 'education', 'learning', 'assignment']):
            doc_type = "Educational Document"
            field = "Education"
        
        # Medical documents
        elif any(word in context_lower for word in ['diagnosis', 'treatment', 'symptoms', 'prescription', 'medical record']):
            doc_type = "Medical Document"
            field = "Healthcare"
        
        # Extract technical terms based on field
        tech_terms = []
        
        if field == "Computer Engineering":
            tech_keywords = ['cnn', 'algorithm', 'opencv', 'machine learning', 'neural network', 
                           'python', 'tensorflow', 'ai', 'computer vision', 'deep learning',
                           'programming', 'software', 'system', 'framework', 'implementation']
        elif field == "Medical Research" or field == "Healthcare":
            tech_keywords = ['clinical', 'patient', 'treatment', 'diagnosis', 'medical', 
                           'healthcare', 'therapy', 'pharmaceutical', 'symptoms', 'disease',
                           'medication', 'prescription', 'clinical trial', 'health']
        elif field == "Business/Finance" or field == "Business Research":
            tech_keywords = ['revenue', 'profit', 'roi', 'kpi', 'analysis', 'growth', 
                           'market', 'strategy', 'budget', 'investment', 'sales',
                           'financial', 'business', 'management', 'performance']
        elif field == "Legal":
            tech_keywords = ['contract', 'clause', 'liability', 'terms', 'agreement', 
                           'compliance', 'regulation', 'jurisdiction', 'legal',
                           'law', 'court', 'rights', 'obligations']
        elif field == "Education" or field == "Educational Research":
            tech_keywords = ['learning', 'teaching', 'education', 'student', 'curriculum',
                           'pedagogy', 'assessment', 'academic', 'course', 'instruction']
        else:
            tech_keywords = ['analysis', 'method', 'process', 'system', 'framework', 
                           'approach', 'model', 'structure', 'development', 'implementation']
        
        for term in tech_keywords:
            if term in context_lower:
                tech_terms.append(term.title())
        
        # Extract key phrases with enhanced detection
        sentences = re.split(r'[.!?]+', context)
        key_sentences = []
        
        # Field-specific important words
        if field == "Computer Engineering":
            important_words = ['algorithm', 'system', 'method', 'implement', 'develop', 'cnn', 'opencv', 'software']
        elif field == "Medical Research" or field == "Healthcare":
            important_words = ['patient', 'treatment', 'clinical', 'medical', 'health', 'study', 'diagnosis']
        elif field == "Business/Finance" or field == "Business Research":
            important_words = ['revenue', 'profit', 'growth', 'market', 'strategy', 'performance', 'business']
        elif field == "Legal":
            important_words = ['contract', 'agreement', 'terms', 'legal', 'clause', 'compliance']
        elif field == "Education" or field == "Educational Research":
            important_words = ['learning', 'education', 'student', 'teaching', 'curriculum']
        else:
            important_words = ['objective', 'purpose', 'methodology', 'result', 'conclusion', 'finding']
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in important_words):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 20 and not clean_sentence.startswith('[From'):
                    key_sentences.append(clean_sentence)
        
        # Extract numbers/statistics (useful for business/research docs)
        numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', context)
        important_numbers = [num for num in numbers if any(char in num for char in ['%', '.']) or (num.isdigit() and int(num) > 50)]
        
        # Extract dates
        dates = re.findall(r'\b\d{4}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', context)
        
        return {
            'doc_type': doc_type,
            'field': field,
            'tech_terms': tech_terms[:8],  # Top 8 terms
            'key_sentences': key_sentences[:4],  # Top 4 sentences
            'important_numbers': important_numbers[:5],  # Top 5 numbers
            'dates': dates[:3]  # Top 3 dates
        }
    
    def create_dynamic_response_for_any_doc(self, query: str, context: str, doc_name: str, info: Dict) -> str:
        """Create dynamic responses that adapt to any document type"""
        
        # Get field-specific emoji and description
        field_info = {
            "Computer Engineering": {"emoji": "💻", "desc": "Technology & Engineering", "color": "blue"},
            "Medical Research": {"emoji": "🏥", "desc": "Healthcare & Medicine", "color": "red"},
            "Healthcare": {"emoji": "🏥", "desc": "Healthcare & Medicine", "color": "red"},
            "Business/Finance": {"emoji": "📊", "desc": "Business & Finance", "color": "green"},
            "Business Research": {"emoji": "📊", "desc": "Business & Finance", "color": "green"},
            "Legal": {"emoji": "⚖️", "desc": "Legal & Compliance", "color": "purple"},
            "Education": {"emoji": "🎓", "desc": "Educational Content", "color": "orange"},
            "Educational Research": {"emoji": "🎓", "desc": "Educational Research", "color": "orange"},
            "Academic Research": {"emoji": "📚", "desc": "Academic Research", "color": "navy"},
            "Psychology/Social Science": {"emoji": "🧠", "desc": "Psychology & Social Sciences", "color": "teal"},
            "Technical Documentation": {"emoji": "🔧", "desc": "Technical Documentation", "color": "gray"},
            "General": {"emoji": "📄", "desc": "General Document", "color": "black"}
        }
        
        field_emoji = field_info.get(info['field'], {}).get('emoji', '📄')
        field_desc = field_info.get(info['field'], {}).get('desc', 'General Content')
        
        # Create dynamic sections based on what's available
        response_parts = []
        
        # Header
        response_parts.append(f"## {field_emoji} Smart Document Analysis")
        response_parts.append(f"**Document:** {doc_name}")
        response_parts.append(f"**Type:** {info['doc_type']}")
        response_parts.append(f"**Field:** {field_desc}")
        response_parts.append("---")
        
        # Key Information (always show)
        response_parts.append("### 📋 Key Information")
        if info['key_sentences']:
            response_parts.append(f"*{info['key_sentences'][0]}*")
        else:
            response_parts.append("*Document content analysis in progress...*")
        response_parts.append("")
        
        # Technical/Field-specific Terms (if available)
        if info['tech_terms']:
            if info['field'] in ["Business/Finance", "Business Research"]:
                response_parts.append("### 💼 Business Terms Identified")
            elif info['field'] in ["Medical Research", "Healthcare"]:
                response_parts.append("### 🏥 Medical Terms Identified")
            elif info['field'] == "Computer Engineering":
                response_parts.append("### 💻 Technical Terms Identified")
            elif info['field'] == "Legal":
                response_parts.append("### ⚖️ Legal Terms Identified")
            elif info['field'] in ["Education", "Educational Research"]:
                response_parts.append("### 🎓 Educational Terms Identified")
            else:
                response_parts.append("### 🔧 Key Terms Identified")
            
            # Format terms nicely
            term_list = " • ".join(info['tech_terms'])
            response_parts.append(f"**{term_list}**")
            response_parts.append("")
        
        # Important Numbers/Statistics (if available)
        if info['important_numbers']:
            response_parts.append("### 📊 Key Numbers/Statistics")
            number_list = " • ".join(info['important_numbers'])
            response_parts.append(f"**{number_list}**")
            response_parts.append("")
        
        # Dates (if available)
        if info['dates']:
            response_parts.append("### 📅 Important Dates")
            date_list = " • ".join(info['dates'])
            response_parts.append(f"**{date_list}**")
            response_parts.append("")
        
        # Additional Key Content (if available)
        if len(info['key_sentences']) > 1:
            response_parts.append("### 📖 Additional Key Content")
            for i, sentence in enumerate(info['key_sentences'][1:3], 1):  # Show 2 more sentences
                truncated = sentence[:120] + "..." if len(sentence) > 120 else sentence
                response_parts.append(f"**{i}.** {truncated}")
            response_parts.append("")
        
        # Field-specific suggested questions
        response_parts.append("### 💡 Suggested Questions for This Document")
        
        if info['field'] == "Computer Engineering":
            questions = [
                "What is the main technical objective of this research?",
                "What algorithms or technologies are implemented?",
                "What is the system architecture or framework?",
                "What are the performance results or evaluation metrics?"
            ]
        elif info['field'] in ["Medical Research", "Healthcare"]:
            questions = [
                "What medical condition or health issue is being addressed?",
                "What treatment methods or interventions are discussed?",
                "What are the clinical findings or health outcomes?",
                "What patient populations or demographics were studied?"
            ]
        elif info['field'] in ["Business/Finance", "Business Research"]:
            questions = [
                "What are the key financial metrics or performance indicators?",
                "What business strategy or approach is being discussed?",
                "What market trends or competitive analysis is included?",
                "What are the revenue projections or financial forecasts?"
            ]
        elif info['field'] == "Legal":
            questions = [
                "What are the main legal terms and conditions?",
                "What obligations or responsibilities are outlined?",
                "What compliance requirements or regulations apply?",
                "What are the key clauses or legal provisions?"
            ]
        elif info['field'] in ["Education", "Educational Research"]:
            questions = [
                "What learning objectives or educational goals are described?",
                "What teaching methods or pedagogical approaches are used?",
                "What student outcomes or assessment criteria are mentioned?",
                "What curriculum or course content is covered?"
            ]
        elif info['field'] == "Technical Documentation":
            questions = [
                "What are the main procedures or instructions?",
                "What technical specifications or requirements are listed?",
                "What troubleshooting or maintenance steps are provided?",
                "What safety or operational guidelines are included?"
            ]
        else:
            questions = [
                "What is the main objective or purpose of this document?",
                "What methodology or approach was used?",
                "What are the key findings or main conclusions?",
                "What recommendations or next steps are suggested?"
            ]
        
        for i, q in enumerate(questions, 1):
            response_parts.append(f"**{i}.** *\"{q}\"*")
        
        response_parts.append("")
        response_parts.append("---")
        response_parts.append("*🤖 Dynamic analysis automatically adapts to your document type and content. For detailed AI-powered insights with full context understanding, upgrade to full mode.*")
        
        return "\n".join(response_parts)
    
    def create_medicine_research_response(self, query: str, context: str, doc_name: str) -> str:
        """Handle medicine-related questions intelligently"""
        info = self.extract_key_information(context)
        
        if 'cnn' in context.lower() and 'prescription' in context.lower():
            return f"""## 🔍 Medicine Research Analysis

**Document:** {doc_name}

---

### ⚠️ Important Finding
This research does **NOT** test specific medicines. Instead, it's a **{info['field']}** study about prescription technology.

### 🎯 What This Research Actually Studies
• **Prescription Reading Technology** - Using AI to read doctor handwriting  
• **CNN Algorithm** - Machine learning for handwriting recognition  
• **Medical Error Prevention** - Reducing mistakes from illegible prescriptions  
• **OpenCV Integration** - Computer vision for prescription processing  

### ❓ Why No Specific Medicines Are Listed
This is a technology study, not a pharmaceutical study. The research focuses on the **tools to read prescriptions** rather than testing actual medications.

### 🔧 Technologies Identified
{' • '.join(info['tech_terms'][:5]) if info['tech_terms'] else 'CNN • OpenCV • Machine Learning'}

---

### 💡 Better Questions for This Document
• **"How does the CNN algorithm work for prescription reading?"**  
• **"What methodology was used to develop this system?"**  
• **"What are the phases of the research framework?"**  
• **"How accurate is the handwriting recognition system?"**  

---
*🤖 This smart analysis is based on document content patterns. For detailed technical explanations, consider upgrading to full AI mode.*"""
        
        elif 'medicine' in query.lower():
            return self.create_dynamic_response_for_any_doc(query, context, doc_name, info)
        
        return self.create_dynamic_response_for_any_doc(query, context, doc_name, info)
    
    def create_methodology_response(self, query: str, context: str, doc_name: str) -> str:
        """Handle methodology questions intelligently"""
        info = self.extract_key_information(context)
        
        field_emoji = "💻" if info['field'] == "Computer Engineering" else "📋"
        
        return f"""## {field_emoji} Methodology Analysis

**Document:** {doc_name}  
**Research Type:** {info['doc_type']}  
**Field:** {info['field']}

---

### 🔬 Methodological Framework Identified

**Primary Approach:**  
{info['key_sentences'][0] if len(info['key_sentences']) > 0 else 'Multi-phase research framework with systematic data collection and analysis'}

**Key Methodology Components:**
{f"• {info['key_sentences'][1]}" if len(info['key_sentences']) > 1 else "• Structured data collection procedures"}
{f"• {info['key_sentences'][2]}" if len(info['key_sentences']) > 2 else "• Systematic analysis and validation methods"}

### 🔧 Technical Approaches
**{' • '.join(info['tech_terms'][:6]) if info['tech_terms'] else 'Systematic research methods and analytical frameworks'}**

### 📊 Research Components
• **Data Collection:** Survey methods, literature review, empirical data gathering  
• **Analysis Methods:** Statistical analysis, algorithm development, performance evaluation  
• **Validation:** Testing procedures, accuracy measurements, system validation  

{f"### 📅 Timeline: **{' • '.join(info['dates'])}**" if info['dates'] else ""}

---

### 💡 Follow-up Methodology Questions
• **"What specific data collection methods were used?"**  
• **"How was the system or algorithm validated?"**  
• **"What are the detailed steps in each research phase?"**  
• **"What metrics were used to measure success?"**  

---
*🔬 This methodology analysis extracts procedural information from document patterns. For detailed step-by-step procedures, upgrade to full AI mode.*"""
    
    def create_objective_response(self, query: str, context: str, doc_name: str) -> str:
        """Handle objective/purpose questions intelligently"""
        info = self.extract_key_information(context)
        
        field_emoji = {
            "Computer Engineering": "💻",
            "Medical Research": "🏥", 
            "Business/Finance": "📊",
            "Legal": "⚖️",
            "Education": "🎓"
        }.get(info['field'], "🎯")
        
        return f"""## {field_emoji} Research Objective Analysis

**Document:** {doc_name}  
**Type:** {info['doc_type']}  
**Field:** {info['field']}

---

### 🎯 Primary Research Objective

{info['key_sentences'][0] if info['key_sentences'] else 'To develop and implement innovative solutions addressing key challenges in the field'}

### 🔍 Problem Being Addressed
{info['key_sentences'][1] if len(info['key_sentences']) > 1 else 'Addressing current limitations and improving existing processes through systematic research and development'}

### 🛠️ Technical Objectives
{f"**Key Technologies:** {' • '.join(info['tech_terms'][:5])}" if info['tech_terms'] else "**Approach:** Systematic methodology with comprehensive analysis"}

• Develop robust and efficient solutions  
• Implement advanced methodological approaches  
• Validate effectiveness through rigorous testing  
• Provide practical applications and improvements  

### 📈 Expected Outcomes
• Enhanced performance and accuracy  
• Improved efficiency and usability  
• Reduced errors and enhanced reliability  
• Practical implementation for real-world applications  

{f"### 📊 Key Metrics: **{' • '.join(info['important_numbers'])}**" if info['important_numbers'] else ""}

---

### 💡 Related Objective Questions
• **"What specific problems does this research solve?"**  
• **"What are the expected benefits and impacts?"**  
• **"How does this advance the current state of knowledge?"**  
• **"What are the practical applications of this research?"**  

---
*🎯 This objective analysis interprets research goals from document content. For comprehensive research objectives and detailed explanations, upgrade to full AI mode.*"""
    
    def create_demo_response(self, query: str, context: str, prompt_type: str = "default") -> str:
        """
        Create a smart demo response based on the context and query type
        
        Args:
            query (str): User question
            context (str): Document context
            prompt_type (str): Type of response needed
            
        Returns:
            str: Smart demo response
        """
        # Find document name
        doc_match = re.search(r'\[From ([^\]]+)', context)
        doc_name = doc_match.group(1) if doc_match else "the uploaded document"
        
        # Get document info
        info = self.extract_key_information(context)
        
        # Analyze query intent
        query_lower = query.lower()
        
        # Handle different types of questions intelligently
        if any(word in query_lower for word in ['medicine', 'medication', 'drug', 'prescription', 'pharmaceutical']):
            return self.create_medicine_research_response(query, context, doc_name)
        
        elif any(word in query_lower for word in ['methodology', 'method', 'approach', 'procedure', 'process', 'framework']):
            return self.create_methodology_response(query, context, doc_name)
        
        elif any(word in query_lower for word in ['objective', 'purpose', 'goal', 'aim', 'about', 'summary', 'what is']):
            return self.create_objective_response(query, context, doc_name)
        
        elif any(word in query_lower for word in ['phase', 'step', 'stage', 'timeline']):
            return self.create_methodology_response(query, context, doc_name)
        
        else:
            return self.create_dynamic_response_for_any_doc(query, context, doc_name, info)
    
    def generate_response(self, query: str, context: str, 
                         temperature: float = 0.7, 
                         max_tokens: int = 1000,
                         prompt_type: str = "default") -> Optional[str]:
        """
        Generate smart response based on content analysis
        
        Args:
            query (str): User question
            context (str): Relevant document context
            temperature (float): Response creativity (ignored in demo)
            max_tokens (int): Maximum response length (ignored in demo)
            prompt_type (str): Type of prompt
            
        Returns:
            Optional[str]: Generated smart response
        """
        if not context or "No relevant context found" in context:
            return """## ❓ No Relevant Content Found

I couldn't find content in the uploaded document that matches your question.

### 🔍 This could mean:
• The document doesn't contain information about this topic  
• Try rephrasing your question with different keywords  
• The document might need to be re-processed  

### 💡 Suggestions:
• Try asking about general topics from the document  
• Use simpler, more direct questions  
• Check if the document was processed correctly  

### 🎯 Common Questions That Work Well:
• **"What is this document about?"**  
• **"What is the main objective?"**  
• **"What methodology was used?"**  
• **"What are the key findings?"**  

---
*🤖 Tip: The more specific your question relates to the document content, the better the response will be.*"""
        
        try:
            return self.create_demo_response(query, context, prompt_type)
        except Exception as e:
            return f"""## ⚠️ Analysis Error

Sorry, there was an error analyzing your document: {str(e)}

### 🔄 Please try:
• Asking a simpler question  
• Using different keywords  
• Re-uploading the document if needed  

---
*🤖 Smart demo analysis encountered an issue. For more reliable responses, consider upgrading to full AI mode.*"""
    
    def generate_follow_up_questions(self, query: str, response: str, context: str) -> List[str]:
        """Generate smart follow-up questions based on content"""
        info = self.extract_key_information(context)
        query_lower = query.lower()
        
        # Customize based on detected field and query type
        if info['field'] == "Computer Engineering":
            if 'medicine' in query_lower:
                return [
                    "How does this research improve prescription accuracy?",
                    "What machine learning techniques are used?",
                    "What are the system performance metrics?"
                ]
            else:
                return [
                    "What algorithms are implemented in this system?",
                    "How was the system tested and validated?",
                    "What are the technical specifications?"
                ]
        
        elif info['field'] in ["Medical Research", "Healthcare"]:
            return [
                "What patient populations were studied?",
                "What are the clinical implications?",
                "How does this improve patient care?",
                "What are the health outcomes measured?"
            ]
        
        elif info['field'] in ["Business/Finance", "Business Research"]:
            return [
                "What are the financial projections?",
                "What market trends are identified?",
                "How does this impact business strategy?",
                "What are the ROI calculations?"
            ]
        
        elif info['field'] == "Legal":
            return [
                "What are the key legal obligations?",
                "What compliance requirements apply?",
                "What are the potential legal risks?",
                "How do these terms affect agreements?"
            ]
        
        else:
            # General follow-ups based on query type
            if 'methodology' in query_lower:
                return [
                    "What specific steps were taken in the research?",
                    "How was data collected and analyzed?",
                    "What validation methods were used?"
                ]
            elif 'objective' in query_lower:
                return [
                    "What specific problems does this solve?",
                    "What are the expected outcomes?",
                    "How does this advance current knowledge?"
                ]
            else:
                return [
                    "What is the main research methodology?",
                    "What are the key findings or results?",
                    "What practical applications does this have?"
                ]
    
    def validate_api_key(self) -> bool:
        """Always return False in demo mode"""
        return False
    
    def get_available_models(self) -> List[str]:
        """Return demo models"""
        return ["smart-dynamic-demo", "intelligent-analysis", "adaptive-content-aware"]
    
    def count_tokens(self, text: str) -> int:
        """Simple token estimation"""
        return len(text.split())
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Return 0 cost for demo mode"""
        return 0.0