from openai import OpenAI
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Fetch API key from env
api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)


# Send a prompt to GPT-4.0/4.1/3.5
response = client.chat.completions.create(
    model="gpt-4.1-nano",  # or "gpt-4" or "gpt-4.0"
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What GPT model are you, and Hello!"}
    ],
    max_tokens=50,
    temperature=0.7
)

# Print the assistant's response
# print("✅ GPT Response:")
print(f'✅ {response.choices[0].message.content.strip()}')
