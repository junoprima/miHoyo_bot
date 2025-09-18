"""
Discord Bot Notification System
Sends check-in results to guild-specific channels using Discord bot
No more webhooks - uses /set_channel command configured channels
"""
import logging
import asyncio
import os
from typing import Dict, Any, Optional
from database.operations import db_ops

logger = logging.getLogger(__name__)

async def send_discord_notification(guild_id: int, success_data: Dict[str, Any]):
    """
    Send check-in notification to Discord channel configured for this guild
    Uses the channel set by /set_channel command
    """
    try:
        # Get the configured check-in channel for this guild
        channel_id = await db_ops.get_guild_setting(guild_id, "channel_checkin")
        if not channel_id:
            logger.warning(f"No check-in channel configured for guild {guild_id}. Use /set_channel command to configure.")
            return False

        # Import discord here to avoid circular imports
        import discord

        # Get bot instance from the running bot
        # This will be called from main.py which runs alongside the Discord bot
        bot_instance = get_bot_instance()
        if not bot_instance:
            logger.error("Discord bot not available for notifications")
            return False

        # Get the channel
        channel = bot_instance.get_channel(int(channel_id))
        if not channel:
            logger.error(f"Could not find channel {channel_id} in guild {guild_id}")
            return False

        # Create embed
        embed = create_checkin_embed(success_data)

        # Send notification
        await channel.send(embed=embed)
        logger.info(f"Check-in notification sent to {channel.name} in {channel.guild.name}")
        return True

    except Exception as e:
        logger.error(f"Error sending Discord notification: {e}")
        return False

def create_checkin_embed(success_data: Dict[str, Any]):
    """Create Discord embed using original format from before 2025-09-17"""
    import discord
    from datetime import datetime, timezone

    embed_dict = {
        "color": 16748258,
        "title": f"{success_data['assets']['game']} Daily Check-In",
        "author": {
            "name": success_data["name"],
            "icon_url": success_data["assets"]["icon"]
        },
        "fields": [
            {"name": "Nickname", "value": success_data["account"]["nickname"], "inline": True},
            {"name": "UID", "value": success_data["account"]["uid"], "inline": True},
            {"name": "Rank", "value": success_data["account"]["rank"], "inline": True},
            {"name": "Region", "value": success_data["account"]["region"], "inline": True},
            {
                "name": "Today's Reward",
                "value": f"{success_data['award']['name']} x{success_data['award']['count']}",
                "inline": True,
            },
            {"name": "Total Check-Ins", "value": success_data["total"], "inline": True},
            {"name": "Result", "value": success_data["result"], "inline": False},
        ],
        "thumbnail": {"url": success_data["award"]["icon"]},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": f"{success_data['assets']['game']} Daily Check-In"},
    }

    # Convert to discord.Embed
    embed = discord.Embed.from_dict(embed_dict)
    return embed

def get_bot_instance():
    """Get the Discord bot instance - to be implemented by the bot runner"""
    # This will be set by the bot when it starts
    return getattr(get_bot_instance, '_bot_instance', None)

def set_bot_instance(bot):
    """Set the Discord bot instance for notifications"""
    get_bot_instance._bot_instance = bot