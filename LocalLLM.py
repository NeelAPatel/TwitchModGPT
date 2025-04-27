# === LLM FUNCTIONS ===
import subprocess
import config
import os
import re


# DEFAULT_PROMPT = r"""You are a Twitch moderation assistant.

# ## Expected Input:
# "[<username>] <message>" — optionally prefixed with '[MOD] '

# ## Task:
# 1. Determine if the message violates community rules.
# 2. Respond in the exact format:
#    Offensive: yes/no
#    Reason: <short reason>
#    Action: pass / timeout / ban

# ## Filters (trigger phrases or patterns):
# - Contains: "kill yourself", "unalive", "go die"
# - Regex: r"\bfat\b.*\bcow\b"
# - Regex: r"(?i)you're\s+(trash|dogwater|useless)"
# - Spam: multiple emojis in a row, or repeated messages

# ## If Input Does Not Match Expected Format:
# Act as a helpful assistant instead.
# """

# full_prompt = ""

# TODO: THE TITLE/CATEGORY/CHANNEL NAME CAN BE INTEGERATED IN THIS FILE ITSELF. JUST CONFIG THE DEFAULT PROMPT BEFORE WRITING/UPDATING


base_prompt = ""
dynamic_stream_channel = ""
dynamic_stream_title = "" 
dynamic_stream_category = ""
dynamic_stream_specific_goal = "None at this time, follow default procedures"

full_prompt = ""

def load_base_prompt(): 
    global base_prompt
    os.makedirs(config.LLM_LOGS_PATH, exist_ok=True)
    
    if os.path.exists(config.LLM_PROMPT_FILE):
        with open(config.LLM_PROMPT_FILE, "r", encoding="utf-8") as f:
            base_prompt = f.read().strip()
    else: 
        raise Exception("Failed to load Base Prompt to LLM")

def update_prompt_stream_context(channel: str, title: str, category: str): 
    global dynamic_stream_channel
    global dynamic_stream_title
    global dynamic_stream_category
    
    dynamic_stream_channel = channel
    dynamic_stream_title = title
    dynamic_stream_category = category
    
    
def update_prompt_stream_specific_goal(goal: str): 
    global dynamic_stream_specific_goal
    dynamic_stream_specific_goal = goal
    

def assemble_full_prompt(): 
    global full_prompt
    
    
    full_prompt = (
        f"{base_prompt}\n\n"
        f"# === Stream Context (Dynamically Updated) ===\n"
        f"- **Channel/Streamer**: {dynamic_stream_channel}\n"
        f"- **Title**: {dynamic_stream_title}\n"
        f"- **Category**: {dynamic_stream_category}\n\n"
    )
    
    if dynamic_stream_specific_goal != "":
        full_prompt += f"# === Channel-Specific Moderation Goal (Dynamic) ===\n" 
        full_prompt += f"{dynamic_stream_specific_goal}"
        
    
    return full_prompt

def get_full_prompt():
    global full_prompt
    return full_prompt


def query_llm(message: str) -> str:
    prompt = assemble_full_prompt()
    # prompt += f"\n Streamer: {config.CHANNEL} \n Stream Category: {category} \n Stream Title: {title}"
    full_input = f"System: {prompt}\nUser: {message}\nAssistant:"
    try:
        result = subprocess.run(["ollama", "run", config.LLM_MODEL], input=full_input.encode(), stdout=subprocess.PIPE)
        output = result.stdout.decode().strip()
        cleaned = re.sub(r"<think>.*?</think>", "", output, flags=re.DOTALL).strip()
        return cleaned
    except Exception as e:
        return f"[LLM Error: {e}]"



# def assemble_full_prompt():
    
#     return


# def load_system_prompt():
#     global full_prompt
#     os.makedirs(config.LLM_LOGS_PATH, exist_ok=True)
    
#     if os.path.exists(config.LLM_PROMPT_FILE):
#         with open(config.LLM_PROMPT_FILE, "r", encoding="utf-8") as f:
#             full_prompt = f.read().strip()
#             # return full_prompt
#     else: 
#         with open (config.LLM_PROMPT_FILE, "w", encoding="utf-8") as f: 
#             f.write(DEFAULT_PROMPT)
#             full_prompt = DEFAULT_PROMPT
#         # return full_prompt
#     return full_prompt


# def load_filters_into_prompt(): 
#     os.makedirs(config.LLM_LOGS_PATH, exist_ok=True)
    
#     if os.path.exists(config.LLM_FILTERS_FILE):
#         with open(config.LLM_FILTERS_FILE, "r", encoding="utf-8") as f:
#             return f.read().strip()
#     return ""