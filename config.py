import os
from dotenv import load_dotenv

load_dotenv()
ENV_FILE = ".env"
TWITCH_TOKEN = os.getenv("TWITCH_ACCESS_PREFIX_TOKEN")
TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")

# ==== Execution configurator
IGNORE_FILTER_FOR_USERS = ["streamelements", "fossabot", "streamlabs", "moobot", "nightbot", "SELF_BOT_neelerita_dev"]

# TWITCH_CHANNEL_TO_ACCESS="MichiMochievee"
# CHANNEL = os.getenv("TWITCH_CHANNEL_TO_ACCESS").lower()
CHANNEL = "Kkatamina"
CHANNEL_TITLE = ""
CHANNEL_CATEGORY=""
CHANNEL_EMOTE_LIST=""
CHANNEL_EMOTE_PATTERN=""
CHANNEL_GOAL_PROMPT="""Goal: Your main focus is to watch out for messages that are asking for other streamers outside of the current collab. 
Her squad right now: Valorant 5stack w/ Ellum twitch.tv/Ellum ♡ Abe twitch.tv/Abe ♡ John twitch.tv/masayoshi ♡ Ryan twitch.tv/itsRyanHiga.
If you see anyone asking for tarik, rae/valkyrae, syk/sykkuno, that is an offense and should be a timeout and mark 'Goal Offense' as yes, otherwise no.
Usual questions on this specific goal from chat range from "Wheres <streamer>", "when is <streamer> going live", etc etc. Ignore messages that fall outside of this goal with exception of explicit rudeness to the streamer and her friends in collab. 
"""
# === LOCAL LLM CONFIG ===
# LLM_MODEL = "deepseek-r1:7b"
LLM_MODEL = "mistral:latest"

LLM_LOGS_PATH = "logs/llm/"
LLM_PROMPT_FILE = LLM_LOGS_PATH + "modgpt_baseprompt.log"
LLM_FILTERS_FILE = LLM_LOGS_PATH + "modgpt_filters_log.log"

# ==== Terminal Configurator =======
LAUNCH_TERMINAL_WINDOWS = True
RESET_LOGS_ON_START = True

# ====== 7tv emote fetcher ============
EMOTES_7TV_API_URL =f'https://emotes.crippled.dev/v1/channel/{CHANNEL}/7tv'
EMOTES_FFZ_API_URL =f'https://emotes.crippled.dev/v1/channel/{CHANNEL}/ffz'
EMOTES_BTTV_API_URL =f'https://emotes.crippled.dev/v1/channel/{CHANNEL}/bttv'
EMOTES_TWITCH_API_URL =f'https://emotes.crippled.dev/v1/channel/{CHANNEL}/twitch'
EMOTES_ALL_API_URL =f'https://emotes.crippled.dev/v1/channel/{CHANNEL}/all'

