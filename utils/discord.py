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

def create_checkin_embed(data: Dict[str, Any]):
    """Create Discord embed for check-in results"""
    import discord

    # Extract data with fallbacks
    account_name = data.get('account_name', data.get('name', 'Unknown Account'))
    game_name = data.get('game_name', 'Unknown Game')
    reward_name = data.get('reward_name', 'Unknown Reward')
    reward_count = data.get('reward_count', 0)
    total_checkins = data.get('total_checkins', data.get('total', 0))
    already_signed = data.get('already_signed', False)

    # Set color and status based on result
    if already_signed:
        color = 0xFFA500  # Orange
        status = "✅ Already Checked In Today"
        emoji = "⭐"
    else:
        color = 0x00FF00  # Green
        status = "🎉 Check-in Successful!"
        emoji = "🎁"

    embed = discord.Embed(
        title=f"🎮 {game_name} Daily Check-in",
        description=status,
        color=color
    )

    # Account info
    embed.add_field(
        name="👤 Account",
        value=f"`{account_name}`",
        inline=True
    )

    # Reward info
    if reward_name and reward_count:
        embed.add_field(
            name=f"{emoji} Today's Reward",
            value=f"`{reward_name}` x**{reward_count}**",
            inline=True
        )

    # Total check-ins
    embed.add_field(
        name="📅 Total Check-ins",
        value=f"**{total_checkins}**",
        inline=True
    )

    # Footer and timestamp
    embed.set_footer(text="miHoYo Auto Check-in • Use /set_channel to configure notifications")
    embed.timestamp = discord.utils.utcnow()

    return embed

def get_bot_instance():
    """Get the Discord bot instance - to be implemented by the bot runner"""
    # This will be set by the bot when it starts
    return getattr(get_bot_instance, '_bot_instance', None)

def set_bot_instance(bot):
    """Set the Discord bot instance for notifications"""
    get_bot_instance._bot_instance = bot