import config
import requests


def get_7tv_emotes():
    url = config.EMOTES_ALL_API_URL
    response = requests.get(url)

    if response.status_code == 200:
        emote_data = response.json()
        emote_names = [emote["code"] for emote in emote_data]
        return sorted(emote_names)
    else:
        print(f"Failed to fetch emotes: {response.status_code}")
        return []

emotes = sorted(get_7tv_emotes())
print("ALL Emotes:", emotes)
