import os
import openai
from server.logger import logger

import ldclient
from ldclient import Context
from ldclient.config import Config

# Initialize OpenAI client
from dotenv import load_dotenv
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def detect_vaccine_denialism(text: str) -> bool:
    """
    Uses OpenAI's API to determine if a post contains vaccine denialism.
    Returns True if vaccine denialism is detected, False otherwise.
    """


    ldclient.set_config(Config(os.getenv("LAUNCHDARKLY_SDK_KEY")))
    ld_client = ldclient.get()

    context = Context.builder("vaccine-filter-user").build()
    if not ld_client.variation("vaccine_disinformation_filter", context, False):
        print("LaunchDarkly flag is not enabled")
        return False
    try:
        print("LaunchDarkly flag is on!!!!")
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
        print("detect_vaccine_denialism result: ", result)
        return result == "true"
        
    except Exception as e:
        logger.error(f"Error detecting vaccine denialism: {e}")
        return False