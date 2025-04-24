import subprocess
from datetime import datetime
import os

# Cached message history and a default system-level instruction prompt.
history = []
localllm_prompt_log = "localllm_prompt_log.log"
localllm_conversation_log = "localllm_conversation_log.log"

# Define the default system prompt only once
default_system_prompt = (
    "You are a Twitch moderation assistant.\n\n"
    "IF a message follows the format: \"[<username>] <message>\" (optionally prefixed with '[MOD] '), then you must:\n"
    "1. Evaluate the message for rule violations.\n"
    "2. Respond with:\n"
    "   - Offensive: yes/no\n"
    "   - Reason: a very short explanation\n"
    "   - Action: pass / timeout / ban\n\n"
    "IF the message does NOT follow that format, then:\n"
    "- DO NOT respond with Offensive/Reason/Action.\n"
    "- Instead, act as a helpful, general-purpose assistant."
)

# Load system prompt from log file if available
if os.path.exists(localllm_prompt_log):
    with open(localllm_prompt_log, "r", encoding="utf-8") as f:
        loaded_prompt = f.read().strip()
        system_prompt = loaded_prompt if loaded_prompt else default_system_prompt
else:
    # with open(localllm_prompt_log, "r", encoding="utf-8") as f:
    #     f.write(default_system_prompt)
    system_prompt = default_system_prompt
    with open(localllm_prompt_log, "r", encoding="utf-8") as f:
        f.write(default_system_prompt)


def log_conversation_to_file(entry: str):
    """Append a line to the chat log file with timestamp."""
    with open(localllm_conversation_log, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {entry}\n")


def build_prompt():
    """
    Builds a full prompt for the model by combining the system prompt
    with the running chat history. Also stores the system prompt.
    """
    with open(localllm_prompt_log, "w", encoding="utf-8") as f:
        f.write(system_prompt)

    prompt = f"System: {system_prompt}\n"
    for m in history:
        role = "User" if m["role"] == "user" else "Assistant"
        prompt += f"{role}: {m['content']}\n"
    prompt += "Assistant:"
    return prompt


def run_ollama_chat(model: str):
    """
    Handles the main conversation loop with the local LLM via Ollama.
    Supports commands prefixed with ! and normal message prompting.
    """
    global system_prompt

    print(f"\n🧠 Starting chat with model: {model}")
    print("Type '!switch <model>' to change models, '!model' to show current, '!list' to list models, '!prompt' to update prompt, or 'exit' to quit.\n")

    log_conversation_to_file(f"System prompt set: \n{system_prompt}")
    log_conversation_to_file(f"Model: {model}\n---")

    while True:
        user_input = input(">>> ").strip()

        # Commands that should not be processed by the LLM
        if user_input.lower() in {"exit", "quit"}:
            log_conversation_to_file("Session ended.")
            break

        elif user_input.startswith("!replaceprompt"):
            system_prompt = input("Enter new system prompt: ").strip()
            print("✅ System prompt updated.\n")
            log_conversation_to_file(f"System prompt updated: {system_prompt}\n---")
            with open(localllm_prompt_log, "w", encoding="utf-8") as f:
                f.write(system_prompt)
            continue
        
        elif user_input.startswith("!appendprompt"):
            print("Append a new System prompt , the current prompt is given below for reference. Anything entered here will be appended to this prompt.")
            print("Current System Prompt: ")
            print(system_prompt)
            
            appended_system_prompt = input("\nAppend to existing prompt: ").strip()
            system_prompt += f'\n{appended_system_prompt}'
            
            print("✅ System prompt updated.\n")
            log_conversation_to_file(f"System prompt updated: {system_prompt}\n---")
            with open(localllm_prompt_log, "w", encoding="utf-8") as f:
                f.write(system_prompt)
            continue
        
        elif user_input.startswith("!prompt"): 
            print(system_prompt)
            continue

        elif user_input.startswith("!model"):
            print(f"🔍 Current model: {model}\n")
            continue

        elif user_input.startswith("!switch"):
            parts = user_input.split(" ", 1)
            if len(parts) == 2:
                model = parts[1]
                print(f"✅ Switched to model: {model}\n")
                log_conversation_to_file(f"Model switched to: {model}\n---")
            else:
                print("⚠️ Please provide a model name, e.g. '!switch mistral'\n")
            continue

        elif user_input.startswith("!list"):
            try:
                result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
                print("📦 Available models:\n" + result.stdout)
            except Exception as e:
                print(f"❌ Failed to list models: {e}\n")
            continue

        # Append the user's message to the chat history
        history.append({"role": "user", "content": user_input})
        log_conversation_to_file(f"User: {user_input}")
        full_prompt = build_prompt()

        result = subprocess.run(
            ["ollama", "run", model],
            input=full_prompt.encode(),
            stdout=subprocess.PIPE
        )

        output = result.stdout.decode().strip()
        history.append({"role": "assistant", "content": output})
        log_conversation_to_file(f"Assistant: {output}\n---")

        print("\n" + output + "\n")


def main():
    model = "deepseek-r1:7b"
    run_ollama_chat(model)


if __name__ == "__main__":
    main()
