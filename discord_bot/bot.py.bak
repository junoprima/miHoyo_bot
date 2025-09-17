import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")

# Initialize bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user.name}")
    print("Loading Cogs...")

    # Dynamically load all Cogs from the cogs directory
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog_name = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog_name)
                print(f"Loaded {filename} successfully.")
            except Exception as e:
                print(f"Failed to load {filename}: {e}")

    print("All Cogs loaded!")

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for commands."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument!")
    else:
        raise error

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
