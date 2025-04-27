import aiohttp
import asyncio
import sys
import os
from dotenv import load_dotenv
import config
# ====== Load ENV ======
load_dotenv()

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
CHANNEL_LOGIN = config.CHANNEL  # fallback default

if not TWITCH_CLIENT_ID or not TWITCH_ACCESS_TOKEN:
    print("❌ Missing TWITCH_CLIENT_ID or TWITCH_ACCESS_TOKEN in your .env file.")
    sys.exit(1)





async def fetch_stream_info(channel_login: str):
    async with aiohttp.ClientSession() as session:
        try:
            user_id = await get_user_id(session, channel_login)
        except Exception as e:
            print(f"❌ Critical error while fetching user ID: {e}")
            sys.exit(1)

        url = f"https://api.twitch.tv/helix/streams?user_id={user_id}"
        headers = {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}"
        }
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                print(f"❌ Failed to fetch stream info. Status: {resp.status}")
                error_text = await resp.text()
                print(f"Response Text: {error_text}")
                sys.exit(1)

            data = await resp.json()

            if not data.get("data"):
                print(f"⚠️ Streamer '{channel_login}' is currently OFFLINE.")
                return "Offline", "N/A"
            
            stream = data["data"][0]
            return stream["title"], stream["game_name"]


async def main():
    print(f"🔎 Fetching stream info for channel: {CHANNEL_LOGIN}")
    title, category = await fetch_stream_info(CHANNEL_LOGIN)
    print(f"✅ Stream Title: {title}")
    print(f"✅ Stream Category: {category}")


if __name__ == "__main__":
    asyncio.run(main())
