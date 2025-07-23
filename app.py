import streamlit as st
import openai
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
import os
from dataclasses import dataclass, asdict
import uuid

# Configure page
st.set_page_config(
    page_title="TalentScout - AI Hiring Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

@dataclass
class CandidateInfo:
    """Data class to store candidate information"""
    session_id: str
    full_name: str = ""
    email: str = ""
    phone: str = ""
    years_experience: str = ""
    desired_positions: str = ""
    current_location: str = ""
    tech_stack: List[str] = None
    responses: Dict[str, str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if self.tech_stack is None:
            self.tech_stack = []
        if self.responses is None:
            self.responses = {}
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class HiringAssistant:
    """AI-powered hiring assistant for TalentScout"""
    
    def __init__(self):
        self.conversation_stages = [
            "greeting",
            "basic_info",
            "tech_stack",
            "technical_questions",
            "conclusion"
        ]
        
        self.tech_questions_db = {
            "python": [
                "Explain the difference between list and tuple in Python.",
                "What is a decorator in Python and how would you implement one?",
                "How does Python's garbage collection work?",
                "What are Python generators and when would you use them?",
                "Explain the concept of duck typing in Python."
            ],
            "javascript": [
                "What is the difference between let, const, and var in JavaScript?",
                "Explain closures in JavaScript with an example.",
                "What is the event loop in JavaScript?",
                "How does prototypal inheritance work in JavaScript?",
                "What are Promises and how do they differ from callbacks?"
            ],
            "react": [
                "What is the virtual DOM and how does it work?",
                "Explain the difference between state and props in React.",
                "What are React hooks and why were they introduced?",
                "How would you optimize a React application's performance?",
                "What is the difference between controlled and uncontrolled components?"
            ],
            "django": [
                "Explain Django's MTV architecture.",
                "What is Django ORM and how does it work?",
                "How do you handle database migrations in Django?",
                "What are Django middlewares and how would you create one?",
                "Explain Django's authentication system."
            ],
            "node.js": [
                "What is the event-driven architecture in Node.js?",
                "Explain the difference between synchronous and asynchronous operations in Node.js.",
                "What is middleware in Express.js?",
                "How do you handle errors in Node.js applications?",
                "What are streams in Node.js and when would you use them?"
            ],
            "sql": [
                "What is the difference between INNER JOIN and LEFT JOIN?",
                "Explain database normalization and its benefits.",
                "What are indexes and how do they improve query performance?",
                "How would you optimize a slow SQL query?",
                "What is the difference between DELETE, DROP, and TRUNCATE?"
            ],
            "java": [
                "Explain the concept of Object-Oriented Programming in Java.",
                "What is the difference between abstract classes and interfaces?",
                "How does garbage collection work in Java?",
                "What are Java Collections and which ones would you use when?",
                "Explain the concept of multithreading in Java."
            ],
            "aws": [
                "What are the main AWS compute services and their use cases?",
                "Explain the difference between S3 storage classes.",
                "How would you design a scalable architecture on AWS?",
                "What is AWS Lambda and when would you use it?",
                "How do you secure applications on AWS?"
            ]
        }
    
    def get_system_prompt(self, stage: str, candidate_info: CandidateInfo) -> str:
        """Generate system prompt based on conversation stage"""
        base_prompt = """You are an AI hiring assistant for TalentScout, a technology recruitment agency. 
        You are professional, friendly, and focused on gathering candidate information efficiently.
        
        IMPORTANT RULES:
        1. Stay focused on the hiring process - don't deviate from your purpose
        2. Be concise but thorough in your responses
        3. Always maintain a professional tone
        4. If asked about topics unrelated to hiring, politely redirect to the hiring process
        5. Handle conversation-ending keywords gracefully (goodbye, bye, exit, quit, etc.)
        """
        
        if stage == "greeting":
            return base_prompt + """
            
            CURRENT TASK: Greet the candidate warmly and explain your purpose.
            - Welcome them to TalentScout
            - Briefly explain that you'll help with initial screening
            - Ask for their full name to begin
            """
            
        elif stage == "basic_info":
            return base_prompt + f"""
            
            CURRENT TASK: Collect basic candidate information.
            Candidate's name: {candidate_info.full_name}
            
            Still need to collect:
            - Email address
            - Phone number  
            - Years of experience
            - Desired position(s)
            - Current location
            
            Ask for one piece of information at a time in a conversational manner.
            """
            
        elif stage == "tech_stack":
            return base_prompt + f"""
            
            CURRENT TASK: Collect the candidate's tech stack.
            Candidate: {candidate_info.full_name}
            
            Ask them to list their technical skills including:
            - Programming languages
            - Frameworks
            - Databases
            - Tools and technologies
            
            Be encouraging and ask for specific technologies they're comfortable with.
            """
            
        elif stage == "technical_questions":
            return base_prompt + f"""
            
            CURRENT TASK: Ask technical questions based on their tech stack.
            Candidate: {candidate_info.full_name}
            Tech Stack: {', '.join(candidate_info.tech_stack)}
            
            Ask relevant technical questions to assess their proficiency.
            Be encouraging and provide feedback on their responses.
            """
            
        elif stage == "conclusion":
            return base_prompt + f"""
            
            CURRENT TASK: Conclude the conversation professionally.
            Candidate: {candidate_info.full_name}
            
            - Thank them for their time
            - Explain next steps in the hiring process
            - Provide contact information if needed
            - End on a positive note
            """
        
        return base_prompt
    
    def generate_response(self, user_input: str, candidate_info: CandidateInfo, stage: str) -> str:
        """Generate AI response using OpenAI API or fallback logic"""
        
        # Check for conversation-ending keywords
        ending_keywords = ["goodbye", "bye", "exit", "quit", "end", "stop", "thanks", "thank you"]
        if any(keyword in user_input.lower() for keyword in ending_keywords):
            return self.get_conclusion_response(candidate_info)
        
        # Use OpenAI API if available, otherwise use fallback logic
        try:
            if os.getenv("OPENAI_API_KEY"):
                return self.generate_openai_response(user_input, candidate_info, stage)
            else:
                return self.generate_fallback_response(user_input, candidate_info, stage)
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return self.generate_fallback_response(user_input, candidate_info, stage)
    
    def generate_openai_response(self, user_input: str, candidate_info: CandidateInfo, stage: str) -> str:
        """Generate response using OpenAI API"""
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        system_prompt = self.get_system_prompt(stage, candidate_info)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def generate_fallback_response(self, user_input: str, candidate_info: CandidateInfo, stage: str) -> str:
        """Generate response using rule-based fallback logic"""
        
        if stage == "greeting":
            if not candidate_info.full_name:
                return """Hello! Welcome to TalentScout! 🎯 
                
I'm your AI hiring assistant, and I'm here to help with your initial screening process. I'll gather some basic information about you and ask a few technical questions based on your expertise.

To get started, could you please tell me your full name?"""
        
        elif stage == "basic_info":
            if not candidate_info.email:
                return f"Nice to meet you, {candidate_info.full_name}! Could you please provide your email address?"
            elif not candidate_info.phone:
                return "Great! Now, what's your phone number?"
            elif not candidate_info.years_experience:
                return "Perfect! How many years of professional experience do you have?"
            elif not candidate_info.desired_positions:
                return "Excellent! What position(s) are you interested in applying for?"
            elif not candidate_info.current_location:
                return "Almost done with basic info! What's your current location?"
            else:
                return f"Thank you for providing all the basic information, {candidate_info.full_name}! Now let's move on to your technical skills."
        
        elif stage == "tech_stack":
            return f"""Thanks for that information, {candidate_info.full_name}! 

Now I'd like to learn about your technical skills. Could you please list the technologies you're proficient in? This might include:

• Programming languages (Python, JavaScript, Java, etc.)
• Frameworks (React, Django, Node.js, etc.)  
• Databases (SQL, MongoDB, etc.)
• Tools and platforms (AWS, Docker, Git, etc.)

Please list as many as you're comfortable with!"""
        
        elif stage == "technical_questions":
            return self.generate_technical_questions(candidate_info)
        
        elif stage == "conclusion":
            return self.get_conclusion_response(candidate_info)
        
        return "I'm here to help with your application process. Could you please provide the information I requested?"
    
    def generate_technical_questions(self, candidate_info: CandidateInfo) -> str:
        """Generate technical questions based on candidate's tech stack"""
        if not candidate_info.tech_stack:
            return "I notice you haven't specified your tech stack yet. Could you please list the technologies you're proficient in?"
        
        questions = []
        for tech in candidate_info.tech_stack[:3]:  # Limit to 3 technologies
            tech_lower = tech.lower()
            if tech_lower in self.tech_questions_db:
                # Get 2 questions per technology
                tech_questions = self.tech_questions_db[tech_lower][:2]
                questions.extend([f"**{tech}**: {q}" for q in tech_questions])
        
        if not questions:
            return f"""Great tech stack, {candidate_info.full_name}! 

I'd like to ask you a few general technical questions:

1. **Problem Solving**: Describe your approach to debugging a complex technical issue.

2. **Best Practices**: What coding standards and best practices do you follow in your development work?

3. **Learning**: How do you stay updated with new technologies and industry trends?

Please answer these questions to the best of your ability."""
        
        question_text = f"""Excellent, {candidate_info.full_name}! Based on your tech stack, I have some technical questions for you:

""" + "\n\n".join([f"{i+1}. {q}" for i, q in enumerate(questions[:5])])
        
        question_text += "\n\nPlease answer these questions to demonstrate your technical knowledge."
        
        return question_text
    
    def get_conclusion_response(self, candidate_info: CandidateInfo) -> str:
        """Generate conclusion response"""
        return f"""Thank you so much for your time, {candidate_info.full_name}! 

I've gathered all the necessary information for your initial screening:
✅ Personal Information
✅ Professional Background  
✅ Technical Skills Assessment

**Next Steps:**
1. Our recruitment team will review your responses within 2-3 business days
2. If your profile matches our current openings, we'll contact you via email ({candidate_info.email}) or phone ({candidate_info.phone})
3. The next stage would be a detailed technical interview with our client companies

**Questions?** Feel free to reach out to us at careers@talentscout.com

Best of luck with your job search! 🚀"""

    def extract_info_from_input(self, user_input: str, candidate_info: CandidateInfo, stage: str):
        """Extract and update candidate information from user input"""
        
        if stage == "greeting" and not candidate_info.full_name:
            # Extract name (simple heuristic)
            name_patterns = [
                r"my name is ([a-zA-Z\s]+)",
                r"i'm ([a-zA-Z\s]+)",
                r"i am ([a-zA-Z\s]+)",
                r"^([a-zA-Z\s]+)$"
            ]
            for pattern in name_patterns:
                match = re.search(pattern, user_input.lower())
                if match:
                    candidate_info.full_name = match.group(1).title().strip()
                    break
        
        elif stage == "basic_info":
            # Extract email
            if not candidate_info.email:
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', user_input)
                if email_match:
                    candidate_info.email = email_match.group()
            
            # Extract phone
            if not candidate_info.phone:
                phone_match = re.search(r'[\+]?[1-9]?[\d\s\-\(\)]{10,}', user_input)
                if phone_match:
                    candidate_info.phone = phone_match.group().strip()
            
            # Extract years of experience
            if not candidate_info.years_experience:
                exp_patterns = [
                    r'(\d+)\s*years?',
                    r'(\d+)\s*yrs?',
                    r'(\d+)\s*year',
                ]
                for pattern in exp_patterns:
                    match = re.search(pattern, user_input.lower())
                    if match:
                        candidate_info.years_experience = match.group(1) + " years"
                        break
            
            # Extract position (if not already set and not asking for experience)
            if (not candidate_info.desired_positions and 
                not candidate_info.years_experience and 
                len(user_input.split()) > 2 and 
                not any(word in user_input.lower() for word in ['year', 'experience', 'month'])):
                candidate_info.desired_positions = user_input.strip()
            
            # Extract location (if not already set and all other info is complete)
            if (not candidate_info.current_location and 
                candidate_info.email and candidate_info.phone and 
                candidate_info.years_experience and candidate_info.desired_positions and
                len(user_input.split()) > 1):
                candidate_info.current_location = user_input.strip()
        
        elif stage == "tech_stack":
            # Extract technologies from input
            common_techs = [
                "python", "javascript", "java", "c++", "c#", "php", "ruby", "go", "rust", "swift",
                "react", "angular", "vue", "django", "flask", "express", "spring", "laravel",
                "node.js", "nodejs", "next.js", "nuxt.js",
                "sql", "mysql", "postgresql", "mongodb", "redis", "sqlite",
                "aws", "azure", "gcp", "docker", "kubernetes", "git", "jenkins", "terraform"
            ]
            
            user_input_lower = user_input.lower()
            found_techs = []
            
            for tech in common_techs:
                if tech in user_input_lower:
                    found_techs.append(tech.title())
            
            # Also split by common separators and add
            separators = [',', ';', '•', '-', '\n']
            for sep in separators:
                if sep in user_input:
                    parts = [part.strip() for part in user_input.split(sep)]
                    found_techs.extend([part.title() for part in parts if len(part.strip()) > 1])
            
            # Remove duplicates and update
            if found_techs:
                candidate_info.tech_stack = list(set(candidate_info.tech_stack + found_techs))

def main():
    """Main Streamlit application"""
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f0f8ff;
        border-left: 4px solid #4caf50;
        color: #333333;
    }
    .info-panel {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ff9800;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🎯 TalentScout AI Hiring Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Intelligent candidate screening for technology positions</p>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'candidate_info' not in st.session_state:
        st.session_state.candidate_info = CandidateInfo(session_id=str(uuid.uuid4()))
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'current_stage' not in st.session_state:
        st.session_state.current_stage = "greeting"
    
    if 'assistant' not in st.session_state:
        st.session_state.assistant = HiringAssistant()
    
    # Sidebar with candidate info
    with st.sidebar:
        st.header("📋 Candidate Information")
        
        candidate = st.session_state.candidate_info
        
        if candidate.full_name:
            st.write(f"**Name:** {candidate.full_name}")
        if candidate.email:
            st.write(f"**Email:** {candidate.email}")
        if candidate.phone:
            st.write(f"**Phone:** {candidate.phone}")
        if candidate.years_experience:
            st.write(f"**Experience:** {candidate.years_experience}")
        if candidate.desired_positions:
            st.write(f"**Position:** {candidate.desired_positions}")
        if candidate.current_location:
            st.write(f"**Location:** {candidate.current_location}")
        if candidate.tech_stack:
            st.write(f"**Tech Stack:** {', '.join(candidate.tech_stack)}")
        
        st.divider()
        
        # Progress indicator
        stages = ["Greeting", "Basic Info", "Tech Stack", "Questions", "Complete"]
        current_idx = st.session_state.assistant.conversation_stages.index(st.session_state.current_stage)
        
        st.write("**Progress:**")
        for i, stage in enumerate(stages):
            if i <= current_idx:
                st.write(f"✅ {stage}")
            else:
                st.write(f"⏳ {stage}")
        
        # Reset button
        if st.button("🔄 Start New Session"):
            st.session_state.candidate_info = CandidateInfo(session_id=str(uuid.uuid4()))
            st.session_state.conversation_history = []
            st.session_state.current_stage = "greeting"
            st.rerun()
    
    # Main chat interface
    st.header("💬 Chat Interface")
    
    # Display conversation history
    for message in st.session_state.conversation_history:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {message["content"]}</div>', 
                       unsafe_allow_html=True)
    
    # Initial greeting
    if not st.session_state.conversation_history:
        initial_response = st.session_state.assistant.generate_response(
            "", st.session_state.candidate_info, st.session_state.current_stage
        )
        st.session_state.conversation_history.append({"role": "assistant", "content": initial_response})
        st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {initial_response}</div>', 
                   unsafe_allow_html=True)
    
    # User input
    user_input = st.text_input("Type your response here:", key="user_input", placeholder="Enter your message...")
    
    if st.button("Send") and user_input:
        # Add user message to history
        st.session_state.conversation_history.append({"role": "user", "content": user_input})
        
        # Extract information from user input
        st.session_state.assistant.extract_info_from_input(
            user_input, st.session_state.candidate_info, st.session_state.current_stage
        )
        
        # Update conversation stage based on collected information
        candidate = st.session_state.candidate_info
        
        if st.session_state.current_stage == "greeting" and candidate.full_name:
            st.session_state.current_stage = "basic_info"
        elif (st.session_state.current_stage == "basic_info" and 
              candidate.full_name and candidate.email and candidate.phone and 
              candidate.years_experience and candidate.desired_positions and 
              candidate.current_location):
            st.session_state.current_stage = "tech_stack"
        elif st.session_state.current_stage == "tech_stack" and candidate.tech_stack:
            st.session_state.current_stage = "technical_questions"
        elif st.session_state.current_stage == "technical_questions":
            # After a few exchanges, move to conclusion
            tech_exchanges = len([m for m in st.session_state.conversation_history 
                                if m["role"] == "user" and "technical" in str(m).lower()])
            if tech_exchanges >= 2:
                st.session_state.current_stage = "conclusion"
        
        # Generate AI response
        ai_response = st.session_state.assistant.generate_response(
            user_input, st.session_state.candidate_info, st.session_state.current_stage
        )
        
        # Add AI response to history
        st.session_state.conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Rerun to update the display
        st.rerun()
    
    # Instructions panel
    with st.expander("ℹ️ How to use this assistant"):
        st.markdown("""
        **Welcome to TalentScout's AI Hiring Assistant!**
        
        This chatbot will guide you through an initial screening process:
        
        1. **Introduction**: Provide your basic information
        2. **Tech Stack**: Tell us about your technical skills
        3. **Technical Questions**: Answer questions based on your expertise
        4. **Conclusion**: Learn about next steps
        
        **Tips:**
        - Be specific when listing your technical skills
        - Answer technical questions thoroughly
        - Type 'goodbye' or 'exit' to end the conversation anytime
        - Use the sidebar to track your progress
        
        **Privacy Note**: This is a demo application using simulated data processing.
        """)

if __name__ == "__main__":
    main()
