import discord
from discord.ext import commands
from discord import app_commands
from utils.database import (
    update_cookie_in_database,
    delete_cookie_in_database,
    edit_cookie_in_database,
    fetch_all_games,
    get_account_names_for_game
)
from database.operations import db_ops
import logging

logger = logging.getLogger(__name__)


class Cookies(commands.Cog):
    """Enhanced Cog for cookie-related commands with database support"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def game_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for game names"""
        try:
            games = await fetch_all_games()
            return [
                app_commands.Choice(name=game, value=game)
                for game in games
                if current.lower() in game.lower()
            ][:25]  # Discord limit
        except Exception as e:
            logger.error(f"Error in game autocomplete: {e}")
            return []

    async def account_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for account names"""
        try:
            if not interaction.guild:
                return []

            # Get the selected game from the interaction
            game = interaction.namespace.game if hasattr(interaction.namespace, 'game') else None
            if not game:
                return []

            accounts = await get_account_names_for_game(interaction.guild.id, game)
            return [
                app_commands.Choice(name=account, value=account)
                for account in accounts
                if current.lower() in account.lower()
            ][:25]
        except Exception as e:
            logger.error(f"Error in account autocomplete: {e}")
            return []

    @app_commands.command(name="add_cookie", description="Add a new cookie to the database")
    @app_commands.describe(
        game="Select a game",
        account="Enter the account name",
        cookie="Enter the cookie value"
    )
    @app_commands.autocomplete(game=game_autocomplete)
    async def add_cookie(self, interaction: discord.Interaction, game: str, account: str, cookie: str):
        """Add a cookie for a specific game."""
        try:
            # Register user if not exists
            await db_ops.register_user(
                user_id=interaction.user.id,
                username=interaction.user.name,
                discriminator=interaction.user.discriminator
            )

            # Add guild membership
            if interaction.guild:
                await db_ops.add_guild_member(interaction.guild.id, interaction.user.id)

            # Validate inputs
            if len(cookie) < 10:
                await interaction.response.send_message(
                    "❌ Cookie appears to be too short. Please provide a valid cookie.",
                    ephemeral=True
                )
                return

            if not interaction.guild:
                await interaction.response.send_message(
                    "❌ This command can only be used in a server!",
                    ephemeral=True
                )
                return

            # Add cookie to database
            success = await update_cookie_in_database(
                guild_id=interaction.guild.id,
                user_id=interaction.user.id,
                game_name=game,
                account_name=account,
                cookie=cookie
            )

            if success:
                embed = discord.Embed(
                    title="✅ Cookie Added Successfully!",
                    description=f"Account `{account}` for **{game.title()}** has been added.",
                    color=0x2ecc71
                )
                embed.add_field(
                    name="🎮 Game", value=game.title(), inline=True
                )
                embed.add_field(
                    name="👤 Account", value=account, inline=True
                )
                embed.add_field(
                    name="🔐 Security", value="Cookie encrypted & stored securely", inline=False
                )
                embed.set_footer(text=f"Added by {interaction.user.name}")

                await interaction.response.send_message(embed=embed, ephemeral=True)
                logger.info(f"Cookie added: {account} for {game} by {interaction.user.name} in {interaction.guild.name}")
            else:
                await interaction.response.send_message(
                    f"❌ Failed to add cookie for account `{account}` in `{game}`.",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in add_cookie: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while adding the cookie. Please try again.",
                ephemeral=True
            )

    @app_commands.command(name="edit_cookie", description="Edit an existing cookie in the database")
    @app_commands.describe(
        game="Select a game",
        account="Enter the account name",
        new_cookie="Enter the new cookie value"
    )
    @app_commands.autocomplete(game=game_autocomplete, account=account_autocomplete)
    async def edit_cookie(self, interaction: discord.Interaction, game: str, account: str, new_cookie: str):
        """Edit an existing cookie."""
        try:
            if not interaction.guild:
                await interaction.response.send_message(
                    "❌ This command can only be used in a server!",
                    ephemeral=True
                )
                return

            if len(new_cookie) < 10:
                await interaction.response.send_message(
                    "❌ Cookie appears to be too short. Please provide a valid cookie.",
                    ephemeral=True
                )
                return

            success = await edit_cookie_in_database(
                guild_id=interaction.guild.id,
                user_id=interaction.user.id,
                game_name=game,
                account_name=account,
                updated_cookie=new_cookie
            )

            if success:
                embed = discord.Embed(
                    title="✅ Cookie Updated Successfully!",
                    description=f"Account `{account}` for **{game.title()}** has been updated.",
                    color=0x3498db
                )
                embed.add_field(
                    name="🎮 Game", value=game.title(), inline=True
                )
                embed.add_field(
                    name="👤 Account", value=account, inline=True
                )
                embed.set_footer(text=f"Updated by {interaction.user.name}")

                await interaction.response.send_message(embed=embed, ephemeral=True)
                logger.info(f"Cookie updated: {account} for {game} by {interaction.user.name}")
            else:
                await interaction.response.send_message(
                    f"❌ Failed to update cookie for account `{account}` in `{game}`. Account may not exist.",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in edit_cookie: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while updating the cookie. Please try again.",
                ephemeral=True
            )

    @app_commands.command(name="delete_cookie", description="Delete an existing cookie from the database")
    @app_commands.describe(
        game="Select a game",
        account="Enter the account name"
    )
    @app_commands.autocomplete(game=game_autocomplete, account=account_autocomplete)
    async def delete_cookie(self, interaction: discord.Interaction, game: str, account: str):
        """Delete a cookie."""
        try:
            if not interaction.guild:
                await interaction.response.send_message(
                    "❌ This command can only be used in a server!",
                    ephemeral=True
                )
                return

            # Create confirmation embed
            embed = discord.Embed(
                title="⚠️ Confirm Deletion",
                description=f"Are you sure you want to delete account `{account}` for **{game.title()}**?",
                color=0xe74c3c
            )
            embed.add_field(
                name="📝 Note",
                value="This action cannot be undone. You'll need to re-add the cookie manually.",
                inline=False
            )

            # Create confirmation view
            view = ConfirmationView(interaction.user.id, game, account, interaction.guild.id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in delete_cookie: {e}")
            await interaction.response.send_message(
                "❌ An error occurred. Please try again.",
                ephemeral=True
            )


class ConfirmationView(discord.ui.View):
    """Confirmation view for cookie deletion"""

    def __init__(self, user_id: int, game: str, account: str, guild_id: int):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.game = game
        self.account = account
        self.guild_id = guild_id

    @discord.ui.button(label="Confirm Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the command user can confirm this action.", ephemeral=True)
            return

        try:
            success = await delete_cookie_in_database(
                guild_id=self.guild_id,
                user_id=self.user_id,
                game_name=self.game,
                account_name=self.account
            )

            if success:
                embed = discord.Embed(
                    title="✅ Cookie Deleted Successfully!",
                    description=f"Account `{self.account}` for **{self.game.title()}** has been deleted.",
                    color=0x2ecc71
                )
                logger.info(f"Cookie deleted: {self.account} for {self.game} by {interaction.user.name}")
            else:
                embed = discord.Embed(
                    title="❌ Deletion Failed",
                    description=f"Could not delete account `{self.account}` for **{self.game.title()}**. It may not exist.",
                    color=0xe74c3c
                )

            # Disable all buttons
            for item in self.children:
                item.disabled = True

            await interaction.response.edit_message(embed=embed, view=self)

        except Exception as e:
            logger.error(f"Error confirming deletion: {e}")
            await interaction.response.send_message("❌ An error occurred during deletion.", ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the command user can cancel this action.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🚫 Deletion Cancelled",
            description="The cookie deletion has been cancelled.",
            color=0x95a5a6
        )

        # Disable all buttons
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        """Handle timeout"""
        for item in self.children:
            item.disabled = True


async def setup(bot: commands.Bot):
    await bot.add_cog(Cookies(bot))