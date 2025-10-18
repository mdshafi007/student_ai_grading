import os
from google import genai
from google.genai import types

# IMPORTANT: KEEP THIS COMMENT
# Follow these instructions when using this blueprint:
# - Note that the newest Gemini model series is "gemini-2.5-flash" or gemini-2.5-pro"
#   - do not change this unless explicitly requested by the user

class AIGradingClient:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
            self.has_api_key = True
        else:
            self.client = None
            self.has_api_key = False
    
    def generate_feedback(self, assignment_text, filename):
        """
        Generate feedback for a student assignment using Gemini AI.
        Falls back to mock text if API key is not available.
        """
        if not self.has_api_key or not self.client:
            return self._generate_mock_feedback(filename)
        
        try:
            prompt = f"""You are a grading assistant. Read this student's assignment and give constructive, concise feedback and a numeric score (0–100).

Assignment filename: {filename}
Assignment content:
{assignment_text}

Please provide:
1. Constructive feedback focusing on strengths and areas for improvement
2. A numeric score from 0-100
3. Specific suggestions for improvement

Format your response as:
SCORE: [number]
FEEDBACK: [your detailed feedback here]"""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response.text:
                return self._parse_ai_response(response.text)
            else:
                return self._generate_mock_feedback(filename)
                
        except Exception as e:
            print(f"Error generating AI feedback: {e}")
            return self._generate_mock_feedback(filename)
    
    def _parse_ai_response(self, response_text):
        """Parse AI response to extract score and feedback."""
        lines = response_text.strip().split('\n')
        score = None
        feedback = ""
        
        for line in lines:
            if line.startswith('SCORE:'):
                try:
                    score = int(line.replace('SCORE:', '').strip())
                    score = max(0, min(100, score))  # Ensure score is between 0-100
                except:
                    score = 75  # Default score if parsing fails
            elif line.startswith('FEEDBACK:'):
                feedback = line.replace('FEEDBACK:', '').strip()
                # Get remaining lines as part of feedback
                remaining_lines = lines[lines.index(line)+1:]
                if remaining_lines:
                    feedback += '\n' + '\n'.join(remaining_lines)
                break
        
        # If no feedback found after FEEDBACK: line, use entire response
        if not feedback:
            feedback = response_text
            
        # If no score found, assign default
        if score is None:
            score = 75
            
        return {
            'feedback': feedback,
            'score': score
        }
    
    def _generate_mock_feedback(self, filename):
        """Generate mock feedback when API key is not available."""
        return {
            'feedback': f"Mock feedback for {filename}. This is a placeholder response because the Gemini API key is not configured. The assignment shows good effort and understanding of the topic. Consider adding more specific examples and ensuring proper formatting. Overall structure is clear and arguments are well-presented.",
            'score': 78
        }