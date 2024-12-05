import logging
import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

def send_discord_notification(success):
    embed = {
        "color": 16748258,
        "title": f"{success['assets']['game']} Daily Check-In",
        "author": {
            "name": success["name"],
            "icon_url": success["assets"]["icon"]
        },
        "fields": [
            {"name": "Nickname", "value": success["account"]["nickname"], "inline": True},
            {"name": "UID", "value": success["account"]["uid"], "inline": True},
            {"name": "Rank", "value": success["account"]["rank"], "inline": True},
            {"name": "Region", "value": success["account"]["region"], "inline": True},
            {
                "name": "Today's Reward",
                "value": f"{success['award']['name']} x{success['award']['count']}",
                "inline": True,
            },
            {"name": "Total Check-Ins", "value": success["total"], "inline": True},
            {"name": "Result", "value": success["result"], "inline": False},
        ],
        "thumbnail": {"url": success["award"]["icon"]},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": f"{success['assets']['game']} Daily Check-In"},
    }

    payload = {
        "embeds": [embed],
        "username": success["assets"]["author"],
        "avatar_url": success["assets"]["icon"],
    }

    try:
        logging.debug(f"Payload being sent to Discord: {payload}")  # Log payload for debugging
        response = requests.post(DISCORD_WEBHOOK, json=payload)
        response.raise_for_status()
        logging.info(f"Discord notification sent for {success['name']}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Discord notification: {e}")
