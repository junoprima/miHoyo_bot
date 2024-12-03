import discord
from discord.ext import commands
from discord import app_commands
from utils.firestore import update_cookie_in_firestore, delete_cookie_in_firestore, edit_cookie_in_firestore
from utils.autocomplete import game_autocomplete, account_autocomplete

class Cookies(commands.Cog):
    """Cog for cookie-related commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="add_cookie", description="Add a new cookie to Firestore")
    @app_commands.describe(game="Select a game", account="Enter the account name", cookie="Enter the cookie value")
    @app_commands.autocomplete(game=game_autocomplete)
    async def add_cookie(self, interaction: discord.Interaction, game: str, account: str, cookie: str):
        """Add a cookie for a specific game."""
        success = update_cookie_in_firestore(game, [{"name": account, "cookie": cookie}], append=True)
        if success:
            await interaction.response.send_message(f"Cookie for account '{account}' in '{game}' added successfully!")
        else:
            await interaction.response.send_message(f"Failed to add cookie for account '{account}' in '{game}'.")

    @app_commands.command(name="edit_cookie", description="Edit an existing cookie in Firestore")
    @app_commands.describe(game="Select a game", account="Enter the account name", new_cookie="Enter the new cookie value")
    @app_commands.autocomplete(game=game_autocomplete, account=account_autocomplete)
    async def edit_cookie(self, interaction: discord.Interaction, game: str, account: str, new_cookie: str):
        """Edit an existing cookie."""
        success = edit_cookie_in_firestore(game, account, new_cookie)
        if success:
            await interaction.response.send_message(f"Cookie for account '{account}' in '{game}' updated successfully!")
        else:
            await interaction.response.send_message(f"Failed to update cookie for account '{account}' in '{game}'.")

    @app_commands.command(name="delete_cookie", description="Delete an existing cookie from Firestore")
    @app_commands.describe(game="Select a game", account="Enter the account name")
    @app_commands.autocomplete(game=game_autocomplete, account=account_autocomplete)
    async def delete_cookie(self, interaction: discord.Interaction, game: str, account: str):
        """Delete a cookie."""
        success = delete_cookie_in_firestore(game, account)
        if success:
            await interaction.response.send_message(f"Cookie for account '{account}' in '{game}' deleted successfully!")
        else:
            await interaction.response.send_message(f"Failed to delete cookie for account '{account}' in '{game}'.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Cookies(bot))
