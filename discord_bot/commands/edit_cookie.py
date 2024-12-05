from discord import app_commands, Interaction
from utils.firestore import edit_cookie_in_firestore
from utils.autocomplete import game_autocomplete, account_autocomplete
import logging

@app_commands.command(name="edit_cookie", description="Edit an existing cookie in Firestore")
@app_commands.describe(
    game="Select a game",
    account="Select an account",
    new_cookie="Enter the updated cookie value"
)
@app_commands.autocomplete(game=game_autocomplete, account=account_autocomplete)
async def command(interaction: Interaction, game: str, account: str, new_cookie: str):
    """Edits an existing cookie in Firestore."""
    logging.info(f"Executing 'edit_cookie' with game={game}, account={account}, new_cookie={new_cookie}")
    try:
        success = edit_cookie_in_firestore(game, account, new_cookie)
        if success:
            await interaction.response.send_message(
                f"Cookie for account '{account}' in '{game}' updated successfully!"
            )
        else:
            await interaction.response.send_message(
                f"Failed to update cookie for account '{account}' in '{game}'."
            )
    except Exception as e:
        logging.error(f"Error in 'edit_cookie': {e}")
        await interaction.response.send_message(f"Error updating cookie: {e}")
