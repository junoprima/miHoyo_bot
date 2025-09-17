import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from database.connection import init_database, db_manager
from database.operations import db_ops

# Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Initialize bot with enhanced intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True  # For member join events

bot = commands.Bot(command_prefix="!", intents=intents)

logger = logging.getLogger(__name__)


@bot.event
async def on_ready():
    """Bot ready event - initialize database and register existing guilds"""
    logger.info(f"Bot is ready! Logged in as {bot.user.name}")

    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized successfully")

        # Register all existing guilds the bot is in
        logger.info("Registering existing guilds...")
        for guild in bot.guilds:
            try:
                await db_ops.register_guild(
                    guild_id=guild.id,
                    guild_name=guild.name,
                    webhook_url=None  # Will be set up later via commands
                )
                logger.info(f"Registered existing guild: {guild.name} ({guild.id})")
            except Exception as e:
                logger.error(f"Error registering guild {guild.name}: {e}")

        # Load Cogs
        logger.info("Loading Cogs...")
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                cog_name = f"cogs.{filename[:-3]}"
                try:
                    await bot.load_extension(cog_name)
                    logger.info(f"Loaded {filename} successfully.")
                except Exception as e:
                    logger.error(f"Failed to load {filename}: {e}")

        logger.info("All Cogs loaded!")

        # Sync slash commands
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    except Exception as e:
        logger.error(f"Error during bot startup: {e}")


@bot.event
async def on_guild_join(guild):
    """Event triggered when bot joins a new guild"""
    logger.info(f"Bot joined new guild: {guild.name} ({guild.id})")

    try:
        # Register the new guild
        await db_ops.register_guild(
            guild_id=guild.id,
            guild_name=guild.name,
            webhook_url=None
        )

        # Send welcome message to the first available text channel
        welcome_message = await create_welcome_message(guild)

        # Try to find a suitable channel to send welcome message
        channel = None

        # Look for common channel names
        for channel_name in ['general', 'bot-commands', 'commands', 'bots']:
            channel = discord.utils.get(guild.text_channels, name=channel_name)
            if channel and channel.permissions_for(guild.me).send_messages:
                break

        # If no suitable named channel, use the first available channel
        if not channel:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    channel = ch
                    break

        # Send welcome message
        if channel:
            await channel.send(embed=welcome_message)
            logger.info(f"Sent welcome message to {guild.name} in #{channel.name}")
        else:
            logger.warning(f"Could not find suitable channel to send welcome message in {guild.name}")

    except Exception as e:
        logger.error(f"Error handling guild join for {guild.name}: {e}")


@bot.event
async def on_guild_remove(guild):
    """Event triggered when bot leaves a guild"""
    logger.info(f"Bot removed from guild: {guild.name} ({guild.id})")

    # Note: We don't delete guild data immediately in case the bot is re-added
    # Just mark it as inactive
    try:
        guild_obj = await db_ops.get_guild(guild.id)
        if guild_obj:
            await db_ops.set_guild_setting(guild.id, "is_active", "false")
            logger.info(f"Marked guild {guild.name} as inactive")
    except Exception as e:
        logger.error(f"Error handling guild removal for {guild.name}: {e}")


@bot.event
async def on_member_join(member):
    """Event triggered when a user joins a guild"""
    if member.bot:
        return  # Ignore bot accounts

    try:
        # Register the user
        await db_ops.register_user(
            user_id=member.id,
            username=member.name,
            discriminator=member.discriminator
        )

        # Add to guild membership
        await db_ops.add_guild_member(member.guild.id, member.id)

        logger.debug(f"Registered new member: {member.name} in {member.guild.name}")

    except Exception as e:
        logger.error(f"Error registering member {member.name}: {e}")


@bot.event
async def on_interaction(interaction):
    """Global interaction handler for user registration"""
    if interaction.user.bot:
        return

    try:
        # Register user if they interact with the bot
        await db_ops.register_user(
            user_id=interaction.user.id,
            username=interaction.user.name,
            discriminator=interaction.user.discriminator
        )

        # Add to guild membership if in a guild
        if interaction.guild:
            await db_ops.add_guild_member(interaction.guild.id, interaction.user.id)

    except Exception as e:
        logger.debug(f"Error registering user during interaction: {e}")


@bot.event
async def on_command_error(ctx, error):
    """Global error handler for commands."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument!")
    else:
        logger.error(f"Command error: {error}")
        raise error


async def create_welcome_message(guild) -> discord.Embed:
    """Create a welcome embed message for new guilds"""
    embed = discord.Embed(
        title="🎮 Welcome to miHoYo Check-in Bot!",
        description="Thank you for adding me to your server! I can help automate daily check-ins for miHoYo games.",
        color=0x3498db
    )

    embed.add_field(
        name="🚀 Getting Started",
        value=(
            "1. Use `/add_cookie` to add your game accounts\n"
            "2. Set up a webhook URL with `/setup_webhook` (optional)\n"
            "3. Use `/list_accounts` to view your accounts\n"
            "4. Daily check-ins will run automatically!"
        ),
        inline=False
    )

    embed.add_field(
        name="🎯 Supported Games",
        value=(
            "• Genshin Impact\n"
            "• Honkai Impact 3rd\n"
            "• Honkai: Star Rail\n"
            "• Zenless Zone Zero"
        ),
        inline=True
    )

    embed.add_field(
        name="⚙️ Available Commands",
        value=(
            "• `/add_cookie` - Add account\n"
            "• `/edit_cookie` - Edit account\n"
            "• `/delete_cookie` - Remove account\n"
            "• `/list_accounts` - View accounts\n"
            "• `/trigger_checkin` - Manual check-in\n"
            "• `/setup_webhook` - Configure notifications"
        ),
        inline=True
    )

    embed.add_field(
        name="🔐 Privacy & Security",
        value=(
            "Your account cookies are encrypted and stored securely. "
            "Only you can manage your own accounts within this server."
        ),
        inline=False
    )

    embed.set_footer(
        text=f"Added to {guild.name} • Thanks for choosing miHoYo Bot!",
        icon_url=bot.user.avatar.url if bot.user.avatar else None
    )

    embed.set_thumbnail(
        url="https://fastcdn.hoyoverse.com/static-resource-v2/2024/04/12/b700cce2ac4c68a520b15cafa86a03f0_2812765778371293568.png"
    )

    return embed


@bot.command(name="setup_webhook")
@commands.has_permissions(administrator=True)
async def setup_webhook(ctx, webhook_url: str = None):
    """Admin command to set up webhook URL for notifications"""
    if not webhook_url:
        # Show current webhook
        current_webhook = await db_ops.get_guild_webhook(ctx.guild.id)
        if current_webhook:
            await ctx.send(f"Current webhook: `{current_webhook[:50]}...`")
        else:
            await ctx.send("No webhook configured. Use: `!setup_webhook <webhook_url>`")
        return

    try:
        # Validate webhook URL format
        if not webhook_url.startswith("https://discord.com/api/webhooks/"):
            await ctx.send("❌ Invalid webhook URL format!")
            return

        # Update guild webhook
        guild_obj = await db_ops.get_guild(ctx.guild.id)
        if guild_obj:
            await db_ops.register_guild(
                guild_id=ctx.guild.id,
                guild_name=ctx.guild.name,
                webhook_url=webhook_url
            )
            await ctx.send("✅ Webhook URL updated successfully!")
        else:
            await ctx.send("❌ Error: Guild not found in database!")

    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
        await ctx.send("❌ Error setting up webhook!")


@bot.command(name="guild_info")
@commands.has_permissions(administrator=True)
async def guild_info(ctx):
    """Show guild information and statistics"""
    try:
        # Get guild stats
        stats = await db_ops.get_checkin_stats(ctx.guild.id)

        embed = discord.Embed(
            title=f"📊 Guild Statistics - {ctx.guild.name}",
            color=0x2ecc71
        )

        if stats:
            for game_name, game_stats in stats.items():
                embed.add_field(
                    name=f"🎮 {game_name}",
                    value=(
                        f"Total Check-ins: {game_stats['total_checkins']}\n"
                        f"Successful: {game_stats['successful_checkins']}\n"
                        f"Success Rate: {game_stats['success_rate']}%"
                    ),
                    inline=True
                )
        else:
            embed.add_field(
                name="📈 No Statistics Yet",
                value="No check-in data available for this month.",
                inline=False
            )

        webhook_url = await db_ops.get_guild_webhook(ctx.guild.id)
        embed.add_field(
            name="🔗 Webhook Status",
            value="✅ Configured" if webhook_url else "❌ Not configured",
            inline=True
        )

        embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
        await ctx.send(embed=embed)

    except Exception as e:
        logger.error(f"Error getting guild info: {e}")
        await ctx.send("❌ Error retrieving guild information!")


if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)