"""
Database utility functions - replaces utils/firestore.py
Modern SQLite implementation with async support
"""
import logging
from typing import List, Dict, Optional, Any
from database.operations import db_ops

logger = logging.getLogger(__name__)


async def fetch_cookies_from_database() -> Dict[str, List[Dict[str, str]]]:
    """
    Fetch account cookies from database - replaces fetch_cookies_from_firestore()
    Returns data in same format for compatibility
    """
    logger.info("Fetching account cookies from database...")

    try:
        accounts_by_game = await db_ops.get_all_accounts_for_checkin()

        # Convert to legacy format for compatibility
        cookies = {}
        for game_name, accounts in accounts_by_game.items():
            cookies[game_name] = []
            for account in accounts:
                cookies[game_name].append({
                    "name": account.name,
                    "cookie": account.decrypted_cookie
                })

        logger.info(f"Retrieved {sum(len(accs) for accs in cookies.values())} accounts across {len(cookies)} games")
        return cookies

    except Exception as e:
        logger.error(f"Error fetching cookies from database: {e}")
        return {}


async def update_cookie_in_database(guild_id: int, user_id: int, game_name: str,
                                   account_name: str, cookie: str) -> bool:
    """
    Add or update cookie in database - replaces update_cookie_in_firestore()
    """
    try:
        logger.info(f"Updating cookie for {account_name} in {game_name}")
        await db_ops.add_account(guild_id, user_id, game_name, account_name, cookie)
        logger.info(f"Cookie for {account_name} updated successfully")
        return True
    except Exception as e:
        logger.error(f"Error updating cookie for {account_name} in {game_name}: {e}")
        return False


async def delete_cookie_in_database(guild_id: int, user_id: int, game_name: str, account_name: str) -> bool:
    """
    Delete cookie from database - replaces delete_cookie_in_firestore()
    """
    try:
        logger.info(f"Deleting cookie for account '{account_name}' in game '{game_name}'")
        success = await db_ops.delete_account(guild_id, user_id, game_name, account_name)

        if success:
            logger.info(f"Account '{account_name}' deleted successfully from {game_name}")
        else:
            logger.warning(f"Account '{account_name}' not found in {game_name}")

        return success
    except Exception as e:
        logger.error(f"Error deleting cookie for {game_name}: {e}")
        return False


async def edit_cookie_in_database(guild_id: int, user_id: int, game_name: str,
                                 account_name: str, updated_cookie: str) -> bool:
    """
    Edit cookie in database - replaces edit_cookie_in_firestore()
    """
    try:
        logger.info(f"Editing cookie for account '{account_name}' in game '{game_name}'")
        await db_ops.add_account(guild_id, user_id, game_name, account_name, updated_cookie)
        logger.info(f"Account '{account_name}' updated successfully in {game_name}")
        return True
    except Exception as e:
        logger.error(f"Error editing cookie for {game_name}: {e}")
        return False


async def fetch_all_games() -> List[str]:
    """
    Fetch all game names from database - replaces fetch_all_games()
    """
    try:
        logger.info("Fetching all game names...")
        games = await db_ops.get_games()
        game_names = [game.name for game in games]
        logger.info(f"Fetched games: {game_names}")
        return game_names
    except Exception as e:
        logger.error(f"Error fetching games from database: {e}")
        return []


async def get_guild_accounts(guild_id: int, game_name: str) -> List[Dict[str, str]]:
    """
    Get accounts for specific guild and game
    """
    try:
        accounts = await db_ops.get_accounts_by_game(guild_id, game_name)
        return [
            {
                "name": account.name,
                "cookie": account.decrypted_cookie[:20] + "..." if len(account.decrypted_cookie) > 20 else account.decrypted_cookie,
                "uid": account.uid or "Unknown",
                "nickname": account.nickname or "Unknown",
                "rank": str(account.rank) if account.rank else "Unknown",
                "region": account.region or "Unknown"
            }
            for account in accounts
        ]
    except Exception as e:
        logger.error(f"Error fetching guild accounts: {e}")
        return []


async def get_account_names_for_game(guild_id: int, game_name: str) -> List[str]:
    """
    Get account names for autocomplete
    """
    try:
        accounts = await db_ops.get_accounts_by_game(guild_id, game_name)
        return [account.name for account in accounts]
    except Exception as e:
        logger.error(f"Error fetching account names: {e}")
        return []


# Legacy compatibility functions
async def register_guild_if_needed(guild_id: int, guild_name: str, webhook_url: Optional[str] = None):
    """Register guild when bot is added to server"""
    try:
        await db_ops.register_guild(guild_id, guild_name, webhook_url)
        logger.info(f"Guild {guild_name} ({guild_id}) registered successfully")
    except Exception as e:
        logger.error(f"Error registering guild {guild_id}: {e}")


async def register_user_if_needed(user_id: int, username: str, discriminator: Optional[str] = None):
    """Register user when they interact with bot"""
    try:
        await db_ops.register_user(user_id, username, discriminator)
        await db_ops.add_guild_member(guild_id, user_id)  # This needs guild_id context
    except Exception as e:
        logger.error(f"Error registering user {user_id}: {e}")


async def get_guild_webhook_url(guild_id: int) -> Optional[str]:
    """Get webhook URL for guild"""
    try:
        return await db_ops.get_guild_webhook(guild_id)
    except Exception as e:
        logger.error(f"Error getting webhook for guild {guild_id}: {e}")
        return None