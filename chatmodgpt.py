import os
import subprocess
from dotenv import load_dotenv
from twitchio.ext import commands
import asyncio
import traceback
from twitch_bot import TwitchBot
from string_format_wrap import swrap, pwrap, swrap_test
import re
import aiohttp
import config
from terminal_manager import get_log_filename
import os
import traceback
from twitch_bot import TwitchBot, refresh_access_token
from twitchio.errors import AuthenticationError
import sys

# ========= ENV CONFIGURATION =============
# # === FROM ENV ===
# load_dotenv()
# TWITCH_TOKEN = os.getenv("TWITCH_ACCESS_PREFIX_TOKEN")
# TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
# TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
# CHANNEL = os.getenv("TWITCH_CHANNEL_TO_ACCESS").lower()

# # ==== Execution configurator
# IGNORE_FILTER_FOR_USERS = {"streamelements", "fossabot", "streamlabs", "moobot", "nightbot"}

# # === LOCAL LLM CONFIG ===
# # LLM_MODEL = "deepseek-r1:7b"
# LLM_MODEL = "mistral:latest"
# LLM_PROMPT_FILE = "modgpt_prompt_log.log"
# LLM_FILTERS_FILE = "modgpt_filters_log.log"

# # ==== Terminal Configurator =======
# LAUNCH_TERMINAL_WINDOWS = True
# RESET_LOGS_ON_START = True
# terminal_type = "cmd" 

# # ==== Logging File Names =========
# chat_logfile_name = get_log_filename("chat", terminal_type, config.CHANNEL)
# filtered_logfile_name = get_log_filename("filtered", terminal_type, config.CHANNEL)


# if RESET_LOGS_ON_START:
#     open(chat_log, "w").close()
#     open(filtered_log, "w").close()

if __name__ == "__main__":
    print("🟢 Starting Twitch Chat Bot...")

    try:
        bot = TwitchBot()
        bot.run()
    except AuthenticationError:
        print("🔒 Authentication failed. Attempting token refresh...")
        try:
            refresh_access_token()
            print("🔁 Token refreshed. Restarting bot using os.execv()...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"❌ Token refresh failed: {e}")
            traceback.print_exc()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()