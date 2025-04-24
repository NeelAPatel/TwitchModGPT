from dotenv import load_dotenv
from string_format_wrap import swrap, pwrap, swrap_test
from terminal_manager import get_log_filename, print_to_log
from twitchio.ext import commands
import aiohttp
import asyncio
import config
import os
import re
import subprocess
import traceback
from LocalLLM import query_llm, load_system_prompt



# ==== STREAM INFO HELPER FUNCTIONS ========
async def get_user_id(session, channel_login):
    url = f"https://api.twitch.tv/helix/users?login={channel_login}"
    headers = {
        "Client-ID": config.TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {config.TWITCH_ACCESS_TOKEN}"
    }
    async with session.get(url, headers=headers) as resp:
        data = await resp.json()
        return data['data'][0]['id'] if data['data'] else None
    
async def fetch_stream_info(channel_login: str):
    async with aiohttp.ClientSession() as session:
        user_id = await get_user_id(session, channel_login)
        if not user_id:
            return "Unknown", "Unknown"

        url = f"https://api.twitch.tv/helix/streams?user_id={user_id}"
        headers = {
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {config.TWITCH_ACCESS_TOKEN}"
        }
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            if data["data"]:
                stream = data["data"][0]
                return stream["title"], stream["game_name"]
            return "Offline", "N/A"

# async def refresh_token()




class TwitchBot(commands.Bot):
    # Initializes twitch api and accesses into the channel
    def __init__(self):
        super().__init__(
            token=config.TWITCH_TOKEN,
            prefix="!",
            initial_channels=[config.CHANNEL]
        )
        self.target_channel = None  # will be set when bot is ready
        self.title = None
        self.category = None
        
        self.chat_logfile_name = get_log_filename ("chat", "cmd", config.CHANNEL)
        self.filtered_logfile_name = get_log_filename("filtered", "cmd", config.CHANNEL)
        
        
    # When bot is ready, it will send this message + Enable typing into chat
    async def event_ready(self):
        print(f"✅ Logged in as {self.nick}")
        print(f"📡 Connected to channel: {config.CHANNEL}")
        
        # To be able to type in chat
        self.target_channel = self.get_channel(config.CHANNEL)
        self.loop.create_task(self.listen_to_console())
        self.title, self.category = await fetch_stream_info(config.CHANNEL)
        print(f"📺 {config.CHANNEL} is playing {self.category} with title set as '{self.title}'")

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
            msg = f"{"[MOD] " if is_mod else ""}[{user}] {content}"
            print_to_log(self.chat_logfile_name, msg, "a")
            
        except Exception as e:
            print(f"\n❌ ERROR CHAT MESSAGE: [{user}] {repr(content)}")
            traceback.print_exc()
            print("\n📤 Type a message to send to Twitch chat:\n>>> ", end='', flush=True)

        # Check for filtered messages
        if (
            (user.lower() not in config.IGNORE_FILTER_FOR_USERS) and 
            (
                " om " in content.lower()
                or (user.lower() in {"lalabriar", "neelerita"})
                or (is_mod)
            )
        ):
            try:
                msg = f"{"[MOD] " if is_mod else ""}[{user}] {content}"
                print_to_log(self.chat_logfile_name, msg, "a")
            except Exception as e:
                print(f"\n❌ ERROR FILTERED CHAT MESSAGE: [{user}] {repr(content)}")
                traceback.print_exc()
                print("\n📤 Type a message to send to Twitch chat:\n>>> ", end='', flush=True)


        # === LLM Inference For All Messages===
        msg = f'[{user}] {content}'
        ai_response = query_llm(msg, self.title, self.category)
        print(f"🤖 LLM Flagged a message: {swrap("italic", msg)}\n Response: \n {swrap("b", ai_response)}\n")

        
        
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