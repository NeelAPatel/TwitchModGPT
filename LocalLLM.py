# === LLM FUNCTIONS ===
import subprocess
import config
import os
import re


DEFAULT_PROMPT = r"""You are a Twitch moderation assistant.

## Expected Input:
"[<username>] <message>" — optionally prefixed with '[MOD] '

## Task:
1. Determine if the message violates community rules.
2. Respond in the exact format:
   Offensive: yes/no
   Reason: <short reason>
   Action: pass / timeout / ban

## Filters (trigger phrases or patterns):
- Contains: "kill yourself", "unalive", "go die"
- Regex: r"\bfat\b.*\bcow\b"
- Regex: r"(?i)you're\s+(trash|dogwater|useless)"
- Spam: multiple emojis in a row, or repeated messages

## If Input Does Not Match Expected Format:
Act as a helpful assistant instead.
"""

current_prompt = ""


def load_system_prompt():
    os.makedirs(config.LLM_LOGS_PATH, exist_ok=True)
    
    if os.path.exists(config.LLM_PROMPT_FILE):
        with open(config.LLM_PROMPT_FILE, "r", encoding="utf-8") as f:
            current_prompt = f.read().strip()
            # return current_prompt
    else: 
        with open (config.LLM_PROMPT_FILE, "w", encoding="utf-8") as f: 
            f.write(DEFAULT_PROMPT)
            current_prompt = DEFAULT_PROMPT
        # return current_prompt
    return current_prompt


def load_filters_into_prompt(): 
    os.makedirs(config.LLM_LOGS_PATH, exist_ok=True)
    
    if os.path.exists(config.LLM_FILTERS_FILE):
        with open(config.LLM_FILTERS_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def get_current_prompt():
    return current_prompt

def set_current_prompt_without_saving(text):
    return ""

def update_current_prompt_save(text): 
    return ""
    

def append_to_prompt(append_text): 
    current_prompt += f'\n{append_text}'
    
    
# def append_new_filter():

# def append_new_nuance(): 
    
    


def query_llm(message: str, title, category) -> str:
    prompt = load_system_prompt()
    prompt += f"\n Streamer: {config.CHANNEL} \n Stream Category: {category} \n Stream Title: {title}"
    full_input = f"System: {prompt}\nUser: {message}\nAssistant:"
    try:
        result = subprocess.run(["ollama", "run", config.LLM_MODEL], input=full_input.encode(), stdout=subprocess.PIPE)
        output = result.stdout.decode().strip()
        cleaned = re.sub(r"<think>.*?</think>", "", output, flags=re.DOTALL).strip()
        return cleaned
    except Exception as e:
        return f"[LLM Error: {e}]"
