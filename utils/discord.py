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
    """Create Discord embed matching the original prettier style from image.png"""
    import discord
    from datetime import datetime, timezone

    # Extract data with proper fallbacks
    account_name = success_data.get("name", "Unknown")
    game_name = success_data.get("assets", {}).get("game", "Unknown Game")
    game_author = success_data.get("assets", {}).get("author", "miHoYo")
    game_icon = success_data.get("assets", {}).get("icon", "")

    account = success_data.get("account", {})
    nickname = account.get("nickname", "Unknown")
    uid = account.get("uid", "N/A")
    rank = str(account.get("rank", "N/A"))
    region = account.get("region", "N/A")

    award = success_data.get("award", {})
    reward_name = award.get("name", "Unknown Reward")
    reward_count = award.get("count", 0)
    reward_icon = award.get("icon", "")

    total_checkins = str(success_data.get("total", 0))
    result_message = success_data.get("result", "Check-in completed successfully!")

    # Create embed with purple color matching your image
    embed = discord.Embed(
        title=f"{game_name} Daily Check-In",
        color=0x9966CC,  # Purple color from your image
        timestamp=discord.utils.utcnow()
    )

    # Set author (Paimon APP style from your image)
    if game_author and game_icon:
        embed.set_author(
            name=f"{game_author} APP",
            icon_url=game_icon
        )

    # Add account name as description (MazzxE style from your image)
    embed.description = f"**{account_name}**"

    # Add fields in the exact 3x2 grid layout from your image
    # Top row: Nickname, UID, Rank
    embed.add_field(name="Nickname", value=nickname, inline=True)
    embed.add_field(name="UID", value=uid, inline=True)
    embed.add_field(name="Rank", value=rank, inline=True)

    # Bottom row: Region, Today's Reward, Total Check-Ins
    embed.add_field(name="Region", value=region, inline=True)
    embed.add_field(name="Today's Reward", value=f"{reward_name} x{reward_count}", inline=True)
    embed.add_field(name="Total Check-Ins", value=total_checkins, inline=True)

    # Result message (full width, like in your image)
    embed.add_field(name="Result", value=result_message, inline=False)

    # Set thumbnail (Mora icon on the right, like in your image)
    if reward_icon:
        embed.set_thumbnail(url=reward_icon)

    # Footer matching your image format
    embed.set_footer(text=f"{game_name} Daily Check-In")

    return embed

def get_bot_instance():
    """Get the Discord bot instance - to be implemented by the bot runner"""
    # This will be set by the bot when it starts
    return getattr(get_bot_instance, '_bot_instance', None)

def set_bot_instance(bot):
    """Set the Discord bot instance for notifications"""
    get_bot_instance._bot_instance = bot