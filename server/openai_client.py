import os
import openai

# Initialize OpenAI client
from dotenv import load_dotenv
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def detect_vaccine_denialism(text: str) -> bool:
    """
    Uses OpenAI's API to determine if a post contains vaccine denialism.
    Returns True if vaccine denialism is detected, False otherwise.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at detecting vaccine misinformation and denialism. Respond with only 'true' if the text contains vaccine denialism or 'false' if it does not."},
                {"role": "user", "content": text}
            ],
            temperature=0,
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip().lower()
        print("!!!!!RESULT", result)
        return result == "true"
        
    except Exception as e:
        logger.error(f"Error detecting vaccine denialism: {e}")
        return False