from discord import app_commands, Interaction

@app_commands.command(name="test_command", description="Test if the bot is responding")
async def command(interaction: Interaction):
    """Simple test command to check bot functionality."""
    await interaction.response.send_message("Bot is up and running!")
