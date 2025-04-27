from dotenv import load_dotenv
from string_format_wrap import swrap, pwrap, swrap_test
from terminal_manager import get_log_filename
from twitch_bot import TwitchBot
from twitchio.errors import AuthenticationError
import os
import sys
import traceback
import config
import requests
import re

import aiohttp
import asyncio
import sys
import os
from dotenv import load_dotenv
import config
import LocalLLM as locllm


# ==== EMOTE FETCHER ======
def get_all_channel_emotes():

    url = config.EMOTES_ALL_API_URL
    response = requests.get(url)

    if response.status_code == 200:
        emote_data = response.json()
        emote_names = sorted(set(emote["code"] for emote in emote_data if emote.get("code")))
        return emote_names
    else:
        print(f"Failed to fetch emotes: {response.status_code}")
        return []

def emotes_regexify(channel_emotes_list: list): 
    # channel_emotes_list = get_all_channel_emotes()
    escaped = [re.escape(emote) for emote in channel_emotes_list if emote]  # protect special chars
    emote_pattern = re.compile(r'\b(?:' + '|'.join(escaped) + r')\b', re.IGNORECASE)
    
    return emote_pattern


# ==== STREAM INFO FETCHER ======
async def get_user_id(session, channel_name):

    url = f"https://api.twitch.tv/helix/users?login={channel_name}"
    headers = {
        "Client-ID": config.TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {config.TWITCH_ACCESS_TOKEN}"
    }
    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            print(f"❌ Failed to fetch user_id. Status: {resp.status}")
            error_text = await resp.text()
            print(f"Response Text: {error_text}")
            sys.exit(1)
        
        data = await resp.json()
        if not data.get('data'):
            print(f"❌ No user found with login '{channel_name}'. Double-check the channel name.")
            sys.exit(1)
        
        return data['data'][0]['id']

async def fetch_stream_info(channel_name: str):
    async with aiohttp.ClientSession() as session:
        try:
            user_id = await get_user_id(session, channel_name)
        except Exception as e:
            print(f"❌ Critical error while fetching user ID: {e}")
            sys.exit(1)

        url = f"https://api.twitch.tv/helix/streams?user_id={user_id}"
        headers = {
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {config.TWITCH_ACCESS_TOKEN}"
        }
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                print(f"❌ Failed to fetch stream info. Status: {resp.status}")
                error_text = await resp.text()
                print(f"Response Text: {error_text}")
                sys.exit(1)

            data = await resp.json()

            if not data.get("data"):
                print(f"⚠️ Streamer '{channel_name}' is currently OFFLINE.")
                return "Offline", "N/A"
            
            stream = data["data"][0]
            return stream["title"], stream["game_name"]

# === TOKEN REFRESH CHECK ========
# === Token Refresh Logic ===
def refresh_access_token():
    # from dotenv import load_dotenv
    # load_dotenv()
    print("REFRESHING TOKEN...")
    # Fetch current variables
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")
    refresh_token = os.getenv("TWITCH_REFRESH_TOKEN")

    # Formulate parameters for refresh request
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    # Perform POST request for token
    resp = requests.post(url, params=params)
    print(resp)
    print(resp.status_code)
    if resp.status_code != 200:
        raise Exception(f"Failed to refresh token: {resp.text}")
    if resp.status_code == 400 and "invalid_grant" in resp.text:
        raise Exception("❌ Refresh token is invalid. Manual re-login required.")
    
    
    # Update .env file 
    data = resp.json()
    new_access_token = data["access_token"]
    new_refresh_token = data.get("refresh_token", refresh_token)
    new_prefix_token = f"oauth:{new_access_token}"

    update_env_var("TWITCH_ACCESS_TOKEN", new_access_token)
    update_env_var("TWITCH_ACCESS_PREFIX_TOKEN", new_prefix_token)
    update_env_var("TWITCH_REFRESH_TOKEN", new_refresh_token)

    # Update config in-memory too
    config.TWITCH_ACCESS_TOKEN = new_access_token
    config.TWITCH_TOKEN = new_prefix_token

    print("🔁 Twitch token refreshed and .env updated.")
    return new_access_token, new_prefix_token

def update_env_var(key, value):
    updated = False
    lines = []
    with open(config.ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith(f"{key}="):
                lines.append(f"{key}={value}\n")
                updated = True
            else:
                lines.append(line)
    if not updated:
        lines.append(f"{key}={value}\n")
    with open(config.ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
async def validate_or_refresh_token():
    """
    Pings Twitch API to verify if the current access token is valid.
    Refreshes it if needed.
    """
    url = "https://api.twitch.tv/helix/users"
    headers = {
        "Client-ID": config.TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {config.TWITCH_ACCESS_TOKEN}"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 401:
                print("🔒 Token invalid or expired. Refreshing...")
                refresh_access_token()
                print("✅ Token refreshed successfully.")
            elif resp.status == 200:
                print("✅ Twitch token is valid.")
            else:
                raise Exception(f"Unexpected status code from Twitch: {resp.status}")

async def main():
    print(f"✨ Starting Twitch Chat Moderation System for [{config.CHANNEL}]")

    print("⭕ Pre-Flight Twitch Token check:")
    await validate_or_refresh_token()
    # print(f"✅ New Access Token starts with: {new_access_token[:10]}...")
    print("Pre-Flight Twitch Token check: Completed!")
    
    print("\n⭕ 3rd Party Emotes - Loading")
    config.CHANNEL_EMOTE_LIST = get_all_channel_emotes()
    config.CHANNEL_EMOTE_PATTERN = emotes_regexify(config.CHANNEL_EMOTE_LIST)
    print("3rd Party Emotes - Loaded!")
    print(f"   {len(config.CHANNEL_EMOTE_LIST)} emotes found")
    # print(f"   {config.CHANNEL_EMOTE_LIST}")
    print(f"   {config.CHANNEL_EMOTE_PATTERN}")
    print(f"   Pattern Length: {len(config.CHANNEL_EMOTE_PATTERN.pattern)} characters")
    print()
    # print(f"First 500 chars: {config.CHANNEL_EMOTE_PATTERN.pattern[:500]}")
    # print(f"Last 500 chars: {config.CHANNEL_EMOTE_PATTERN.pattern[-500:]}")
        
    print("\n⭕ Stream Info Fetch - Loading")
    config.CHANNEL_TITLE, config.CHANNEL_CATEGORY = await fetch_stream_info(config.CHANNEL)
    print(f"✅ Stream Title: {config.CHANNEL_TITLE}")
    print(f"✅ Stream Category: {config.CHANNEL_CATEGORY}")
    
    
    print("LLM Configuration - Loading")
    locllm.load_base_prompt()
    locllm.update_prompt_stream_context(config.CHANNEL, config.CHANNEL_TITLE, config.CHANNEL_CATEGORY )
    locllm.update_prompt_stream_specific_goal(config.CHANNEL_GOAL_PROMPT)
    locllm.assemble_full_prompt()
    print(swrap("b", f'LLM Prompt: \n{locllm.get_full_prompt()}'))
    
    user_query = """Analyze the system prompt you have been provided.
        - Summarize your overall moderation duties in your own words.
        - Identify if there are any special focuses today based on the stream's context, such as specific game categories, collaborations, or sponsorships.
        - Be concise but precise: 2–5 sentences max.

        Do not just repeat the prompt — explain what you are actually tasked to do today based on it."""
    ai_response = locllm.query_llm(user_query)
    print(swrap("g", f"👤User Query:  {user_query}") + "\n" + swrap("c", f"🤖 LLM: {ai_response}\n\n"))
    
    print("Twitch Bot - Loading")
    bot = TwitchBot()
    # bot.run()
    await bot.start()
    print("Twitch Bot - Loaded!")
    
if __name__ == "__main__":
    asyncio.run(main())   
    

    # # Try to run the bot. If fails --> Refresh token and try again
    # try:
    #     bot = TwitchBot()
    #     bot.run()
    # except AuthenticationError:
    #     print("🔒 Authentication failed. Attempting token refresh...")
    #     try:
    #         refresh_access_token()
    #         print("🔁 Token refreshed. Restarting bot using os.execv()...")
    #         os.execv(sys.executable, [sys.executable] + sys.argv)
            
    #     except Exception as e:
    #         print(f"❌ Token refresh failed: {e}")
    #         traceback.print_exc()
    # except Exception as e:
    #     print(f"❌ Unexpected error: {e}")
    #     traceback.print_exc()