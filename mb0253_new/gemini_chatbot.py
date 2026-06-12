import google.generativeai as genai
import os

class GeminiChatbot:
   def __init__(self, api_key=None):
    if api_key is None:
        api_key = os.getenv('GEMINI_API_KEY', '')
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")
    
    genai.configure(api_key=api_key)
    self.model = genai.GenerativeModel('gemini-2.5-flash')
    self.chat_history = []
    
    def get_home_remedy_advice(self, symptoms):
        """Get home remedy suggestions for given symptoms"""
        try:
            prompt = f"""You are a helpful health assistant providing general home remedy information. 
            
A patient is asking about home remedies for the following symptoms: {symptoms}

Please provide:
1. General home remedies that might help (not medical advice)
2. When to see a doctor
3. Important disclaimers about consulting healthcare professionals

Remember: This is educational information only, not medical advice. Always recommend consulting a healthcare professional."""
            
            response = self.model.generate_content(prompt)
            return {
                'success': True,
                'response': response.text,
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'response': None,
                'error': str(e)
            }
    
    def chat(self, user_message):
        """Continue conversation with chatbot"""
        try:
            # Add context for home remedies
            system_context = """You are a helpful health assistant specializing in general home remedies and wellness information. 
Always:
- Provide educational information only, not medical diagnosis or treatment
- Recommend consulting healthcare professionals for serious conditions
- Include appropriate disclaimers
- Focus on safe, common home remedies
- Ask clarifying questions if needed"""
            
            full_message = f"{system_context}\n\nUser: {user_message}"
            
            response = self.model.generate_content(full_message)
            
            return {
                'success': True,
                'response': response.text,
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'response': None,
                'error': str(e)
            }
    
    def clear_history(self):
        """Clear chat history"""
        self.chat_history = []
