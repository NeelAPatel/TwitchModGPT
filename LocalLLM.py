# === LLM FUNCTIONS ===
import subprocess
import config
import os
import re



def load_system_prompt():
    if os.path.exists(config.LLM_PROMPT_FILE):
        with open(config.LLM_PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""



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


