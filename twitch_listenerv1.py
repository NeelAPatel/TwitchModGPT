import os
import subprocess
from dotenv import load_dotenv
from twitchio.ext import commands
import asyncio
import traceback


# === CONFIGURATION ===
load_dotenv()
TWITCH_TOKEN = os.getenv("TWITCH_ACCESS_PREFIX_TOKEN")
CHANNEL = os.getenv("TWITCH_CHANNEL_TO_ACCESS").lower()
RESET_LOGS_ON_START = True
IGNORE_FILTER_FOR_USERS = {"streamelements", "fossabot", "streamlabs", "moobot", "nightbot"}

# === TERMINAL SETUP ===
terminal_type = "cmd"  # or "powershell" / "wt"


# === LOGGING FILES ===
def get_log_filename(log_type: str, terminal_type: str, channel: str) -> str:
    return f"{log_type}_{terminal_type}_{channel}.log"

# === Create files ===
chat_log = get_log_filename("chat", terminal_type, CHANNEL)
filtered_log = get_log_filename("filtered", terminal_type, CHANNEL)

if RESET_LOGS_ON_START:
    open(chat_log, "w").close()
    open(filtered_log, "w").close()
    

# === TERMINAL LAUNCHERS ===
def open_terminal_cmd(title, filepath):
# Check if a window with the same title is already open
# Use PowerShell to check for existing windows with the title
    try:
        check_cmd = [
            "powershell",
            "-Command",
            f"Get-Process cmd | Where-Object {{$_.MainWindowTitle -like '*{title}*'}}"
        ]
        existing = subprocess.run(check_cmd, capture_output=True, text=True)
        if title.lower() in existing.stdout.lower():
            print(f"⚠️ Terminal '{title}' already open. Skipping new launch.")
            if RESET_LOGS_ON_START:
                open(filepath, "w").close()
            return None
    except Exception as e:
        print(f"❌ Error checking terminal title: {e}")

    # Launch the actual terminal
    return subprocess.Popen(
        f'start "{title}" cmd /k powershell -Command "Clear-Host; Get-Content -Path \\"{filepath}\\" -Wait"',
        shell=True
    )

# def open_terminal_powershell(title, filepath):
#     return subprocess.Popen([
#         "powershell", "-NoExit", "-Command",
#         f"$host.UI.RawUI.WindowTitle = '{title}'; Get-Content -Path '{filepath}' -Wait"
#     ])

# def open_terminal_windows_terminal(title, filepath):
#     return subprocess.Popen([
#         "wt", f'-w 0 nt --title "{title}" powershell -NoExit -Command "Get-Content -Path \'{filepath}\' -Wait"'
#     ])


# --- Open terminals and keep handles ---
if terminal_type == "cmd":
    chat_proc = open_terminal_cmd(f'Twitch Chat - {CHANNEL} - All', chat_log)
    filtered_proc = open_terminal_cmd(f'Filtered Chat {CHANNEL}', filtered_log)

# elif terminal_type == "powershell":
#     chat_proc = open_terminal_powershell("Twitch Chat - All", chat_log)
#     filtered_proc = open_terminal_powershell("Filtered Chat", filtered_log)

# elif terminal_type == "wt":
#     chat_proc = open_terminal_windows_terminal("Twitch Chat - All", chat_log)
#     filtered_proc = open_terminal_windows_terminal("Filtered Chat", filtered_log)

# Main Bot Class
class Bot(commands.Bot):

    # Initializes twitch api and accesses into the channel
    def __init__(self):
        super().__init__(
            token=TWITCH_TOKEN,
            prefix="!",
            initial_channels=[CHANNEL]
        )
        self.target_channel = None  # will be set when bot is ready
        
    # When bot is ready, it will send this message + Enable typing into chat
    async def event_ready(self):
        print(f"✅ Logged in as {self.nick}")
        print(f"📡 Connected to channel: {CHANNEL}")
        
        # To be able to type in chat
        self.target_channel = self.get_channel(CHANNEL)
        self.loop.create_task(self.listen_to_console())

    # When a message is detected in the channel, it will log it. 
    async def event_message(self, message):
        # Fallbacks in case anything is missing
        content = "<NO CONTENT>"
        user = "<UNKNOWN>"
        is_mod = False
        
        # Extract message content
        try:
            content = message.content if message.content else "<NO CONTENT>"
        except Exception as e:
            print(f"\n❌ ERROR: Unable to access message.content")
            traceback.print_exc()
            print("\n📤 Type a message to send to Twitch chat:\n>>> ", end='', flush=True)

        
        # Try to extract author info
        # Handle missing author — assume it's the bot
        if message.author is None:
            user = "SELF_BOT_neelerita_dev"
            is_mod = True  # Assume bot has mod privileges
        else:
            try:
                if message.author is None:
                    raise AttributeError("message.author is None")
                user = message.author.name or "<NO NAME>"
                is_mod = message.author.is_mod
            except Exception as e:
                print(f"\n❌ ERROR: Failed to extract user info.")
                print(f"Content: {repr(content)}")
                print(f"Message raw: {repr(message)}")
                traceback.print_exc()
                print("\n📤 Type a message to send to Twitch chat:\n>>> ", end='', flush=True)

        
        

        # Log all messages
        try:
            with open(chat_log, "a", encoding="utf-8") as f:
                    if is_mod: 
                        m = "[MOD] "
                    else: 
                        m = ""
                    f.write(f"{m}[{user}] {content}\n")
        except Exception as e:
            print(f"\n❌ ERROR CHAT MESSAGE: [{user}] {repr(content)}")
            traceback.print_exc()
            print("\n📤 Type a message to send to Twitch chat:\n>>> ", end='', flush=True)


        # Check for filtered messages
        if (
            (user.lower() not in IGNORE_FILTER_FOR_USERS) and 
            (
                " om " in content.lower()
                or (user.lower() in {"lalabriar", "neelerita"})
                or (is_mod)
            )
        ):
            try:
                with open(filtered_log, "a", encoding="utf-8") as f:
                    if is_mod: 
                        m = "[MOD] "
                    else: 
                        m = ""
                    f.write(f"{m}[{user}] {content}\n")
            except Exception as e:
                print(f"\n❌ ERROR FILTERED CHAT MESSAGE: [{user}] {repr(content)}")
                traceback.print_exc()
                print("\n📤 Type a message to send to Twitch chat:\n>>> ", end='', flush=True)

    # In the background it keeps connection ready to send a message in chat
    async def listen_to_console(self):
        await asyncio.sleep(2)  # slight delay to avoid race condition

        while True:
            try:
                msg = await asyncio.to_thread(input, "\n📤 Type a message to send to Twitch chat: ")
                if msg.strip() and self.target_channel:
                    await self.target_channel.send(msg.strip())
                    print("✅ Sent to chat.")
            except Exception as e:
                print(f"\n❌ Error sending message:\n{e}")
                print("\n📤 Type a message to send to Twitch chat:\n>>> ", end='', flush=True)

# Run bot
if __name__ == "__main__":
    print("🟢 Starting Twitch Chat Bot...")
    bot = Bot()
    bot.run()
