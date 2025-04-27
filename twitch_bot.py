from operator import contains
from dotenv import load_dotenv
from string_format_wrap import swrap, pwrap, swrap_test
from terminal_manager import get_log_filename, open_terminal_cmd, print_to_log
from twitchio.ext import commands
import aiohttp
import asyncio
import config
import os
import re
import subprocess
import traceback
# from LocalLLM import query_llm, load_base_prompt
import LocalLLM as locllm
import sys

from testStreamInfoFetch import fetch_stream_info


class TwitchBot(commands.Bot):
    # Initializes twitch api and accesses into the channel
    def __init__(self):
        super().__init__(
            token=config.TWITCH_TOKEN,
            prefix="!",
            initial_channels=[config.CHANNEL]
        )
        
        # set up logging and tailing        
        self.chat_logfile_name = get_log_filename ("chat", "cmd", config.CHANNEL)
        self.filtered_logfile_name = get_log_filename("filtered", "cmd", config.CHANNEL)
        if config.RESET_LOGS_ON_START:
            open(self.chat_logfile_name, "w").close()
            open(self.filtered_logfile_name, "w").close()
        
        # self.emote_pattern = ""
        
    # When bot is ready, it will send this message + Enable typing into chat
    async def event_ready(self):
        print(f"✅ Logged in as {self.nick}")
        print(f"📡 Connected to channel: {config.CHANNEL}")
        
        # To be able to type in chat
        self.target_channel = self.get_channel(config.CHANNEL)
        self.loop.create_task(self.listen_to_console())



    # When a message is detected in the channel, it will log it. 
    async def event_message(self, message):
        
        # Fallbacks in case anything is missing
        content = "<NO CONTENT>"
        sanitized_content = "<NO CONTENT>"
        user = "<UNKNOWN>"
        is_mod = False
        output_log_msg = ""
        
        # 1. Extract Message content: 
        try:
            content = message.content if message.content else "<NO CONTENT>"
        except Exception as e:
            print(f"\n ERROR: Unable to access message.content")
            traceback.print_exc()
            print("\n📤 Type a message to send to Twitch chat:\n>>> ", end='', flush=True)
        
        #2. Extract Author accounting for self user bot: 
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

        # --- 3. Detect and process emotes ---
        try:
            if config.CHANNEL_EMOTE_PATTERN:
                emote_pattern = config.CHANNEL_EMOTE_PATTERN

                def prefix_emotes(match):
                    return f"[E] {match.group(0)}"

                # Add [E] prefix on matched emotes
                content_with_emote_tags = emote_pattern.sub(prefix_emotes, content)

                # Remove emotes completely for sanitized version
                sanitized_content = emote_pattern.sub("", content).strip()

            else:
                content_with_emote_tags = content
                sanitized_content = content
        except Exception as e:
            print(f"\n❌ ERROR while sanitizing content: {e}")
            traceback.print_exc()
            content_with_emote_tags = content
            sanitized_content = content
    
        # --- 4. Build final output message for logging and LLM ---
        output_log_msg = f"{'[MOD] ' if is_mod else ''}[{user}] {content_with_emote_tags} {{{{{sanitized_content}}}}}"
        
        # Log ALL messages: 
        try:
            # output_log_msg = f"{"[MOD] " if is_mod else ""}[{user}] {content}"
            print_to_log(self.chat_logfile_name, output_log_msg, "a")
            # print(output_log_msg)
        except Exception as e:
            print(f"\n❌ ERROR CHAT MESSAGE: [{user}] {repr(content)}")
            traceback.print_exc()
            print("\n📤 Type a message to send to Twitch chat:\n>>> ", end='', flush=True)
    
            
        # # Filter Bot messages otherwise Pass to LLM
        if user.lower() not in config.IGNORE_FILTER_FOR_USERS or (is_mod):
            # === LLM Inference For All Messages===
                
            ai_response = locllm.query_llm(output_log_msg)
            ai_color_response = ""
            
            
            if ("Goal Offense: yes" in ai_response): 
                ai_color_response = swrap("r", ai_response)
            elif ("Offense: yes" in str(ai_response)):
                ai_color_response = swrap("y", ai_response)
            else: 
                ai_color_response = swrap("c", ai_response)
            
            print(f"🤖 LLM Flagged a message: {swrap("italic", output_log_msg)}\n Response: \n {ai_color_response}\n")


        
        # Remove emotes from chat message
        # content = config.CHANNEL_EMOTE_PATTERN.sub("", content).strip()
        
        
        
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