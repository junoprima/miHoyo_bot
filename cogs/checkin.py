import discord
from discord.ext import commands
from discord import app_commands
from main import run_daily_checkin  # Assuming main.py contains the logic for check-ins

class CheckIn(commands.Cog):
    """Cog for triggering the daily check-in."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="trigger_checkin", description="Manually trigger the daily check-in process")
    async def trigger_checkin(self, interaction: discord.Interaction):
        """Manually trigger the daily check-in process."""
        try:
            await interaction.response.send_message("Daily check-in triggered!")
            run_daily_checkin()
        except Exception as e:
            await interaction.followup.send(f"Failed to trigger check-in: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(CheckIn(bot))
