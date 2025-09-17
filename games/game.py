import logging
import requests
import asyncio
from typing import List, Dict, Any, Optional
from utils.discord import send_discord_notification
from database.operations import db_ops
from games.game import Game  # Import original Game class for compatibility

logger = logging.getLogger(__name__)


class GameManager:
    """Enhanced game manager with database integration and async support"""

    def __init__(self):
        self.session = requests.Session()

    async def process_game_checkins(self, game_name: str, game_config: Dict[str, Any],
                                  accounts: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Process check-ins for all accounts of a specific game"""
        successes = []

        # Create Game instance using original class for compatibility
        game = Game(game_name, game_config, accounts)

        for account in accounts:
            try:
                # Process single account
                result = await self.process_single_account(game, account, game_name)
                if result:
                    successes.append(result)

                # Small delay between accounts to avoid rate limiting
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error processing account {account.get('name', 'Unknown')}: {e}")

                # Log failed check-in to database
                await self.log_failed_checkin(account, game_name, str(e))

        return successes

    async def process_single_account(self, game: Game, account: Dict[str, str],
                                   game_name: str) -> Optional[Dict[str, Any]]:
        """Process check-in for a single account with database logging"""
        try:
            account_name = account.get("name", "Unknown")
            cookie = account.get("cookie", "")

            if not cookie:
                logger.warning(f"No cookie provided for account: {account_name}")
                return None

            logger.info(f"Processing account: {account_name} for {game.full_name}")

            # Get sign info
            sign_info = game.get_sign_info(cookie)
            if not sign_info["success"]:
                error_msg = sign_info.get('message', 'Unknown error')
                logger.warning(f"{account_name}: Failed to retrieve sign info. Reason: {error_msg}")
                await self.log_failed_checkin(account, game_name, error_msg)
                return None

            # Check if already signed in
            if sign_info["data"]["is_signed"]:
                logger.info(f"{account_name}: Already signed in today.")
                await self.log_successful_checkin(account, game_name, None, None, None,
                                                sign_info["data"]["total"], already_signed=True)
                return None

            # Get account details
            ltuid = game.extract_ltuid(cookie)
            if not ltuid:
                error_msg = "ltuid_v2 is missing or invalid in the cookie"
                logger.warning(f"{account_name}: {error_msg}")
                await self.log_failed_checkin(account, game_name, error_msg)
                return None

            account_details = game.get_account_details(cookie, ltuid)
            if not account_details:
                error_msg = "Failed to retrieve account details"
                logger.warning(f"{account_name}: {error_msg}")
                await self.log_failed_checkin(account, game_name, error_msg)
                return None

            # Update account details in database
            await self.update_account_details(account, game_name, account_details)

            # Get awards data
            if not game.awards:
                awards_data = game.get_awards_data(cookie)
                if not awards_data["success"]:
                    error_msg = "Failed to fetch awards data"
                    logger.warning(f"{account_name}: {error_msg}")
                    await self.log_failed_checkin(account, game_name, error_msg)
                    return None
                game.awards = awards_data["data"]

            # Determine today's reward
            total_signed = sign_info["data"]["total"]
            if total_signed >= len(game.awards):
                error_msg = f"Total signed ({total_signed}) exceeds available awards ({len(game.awards)})"
                logger.warning(f"{account_name}: {error_msg}")
                await self.log_failed_checkin(account, game_name, error_msg)
                return None

            award_object = {
                "name": game.awards[total_signed]["name"],
                "count": game.awards[total_signed]["cnt"],
                "icon": game.awards[total_signed]["icon"],
            }

            # Attempt to sign in
            sign_response = game.sign(cookie)
            if not sign_response["success"]:
                error_msg = sign_response.get('message', 'Unknown error')
                logger.warning(f"{account_name}: Failed to sign in. Reason: {error_msg}")
                await self.log_failed_checkin(account, game_name, error_msg)
                return None

            # Log successful check-in
            new_total = sign_info["data"]["total"] + 1
            await self.log_successful_checkin(
                account, game_name, award_object["name"],
                award_object["count"], award_object["icon"], new_total
            )

            # Log success
            logger.info(
                f"{account_name}: Successfully signed in. Today's reward: {award_object['name']} x{award_object['count']}"
            )

            # Prepare success data for Discord notification
            success_data = {
                "platform": game_name,
                "total": new_total,
                "result": game.config["successMessage"],
                "assets": game.config["assets"],
                "account": account_details,
                "award": award_object,
                "name": account_name,
            }

            # Send Discord notification
            send_discord_notification(success_data)

            return success_data

        except Exception as e:
            logger.error(f"Error processing account {account.get('name', 'Unknown')}: {e}")
            await self.log_failed_checkin(account, game_name, str(e))
            return None

    async def log_successful_checkin(self, account: Dict[str, str], game_name: str,
                                   reward_name: Optional[str], reward_count: Optional[int],
                                   reward_icon: Optional[str], total_checkins: int,
                                   already_signed: bool = False):
        """Log successful check-in to database"""
        try:
            # Find account in database
            account_id = await self.get_account_id(account["name"], game_name)
            if account_id:
                await db_ops.log_checkin(
                    account_id=account_id,
                    success=True,
                    reward_name=reward_name,
                    reward_count=reward_count,
                    reward_icon=reward_icon,
                    total_checkins=total_checkins,
                    error_message="Already signed in today" if already_signed else None
                )
        except Exception as e:
            logger.error(f"Error logging successful check-in: {e}")

    async def log_failed_checkin(self, account: Dict[str, str], game_name: str, error_message: str):
        """Log failed check-in to database"""
        try:
            account_id = await self.get_account_id(account["name"], game_name)
            if account_id:
                await db_ops.log_checkin(
                    account_id=account_id,
                    success=False,
                    error_message=error_message
                )
        except Exception as e:
            logger.error(f"Error logging failed check-in: {e}")

    async def update_account_details(self, account: Dict[str, str], game_name: str,
                                   account_details: Dict[str, Any]):
        """Update account details in database"""
        try:
            account_id = await self.get_account_id(account["name"], game_name)
            if account_id:
                await db_ops.update_account_details(
                    account_id=account_id,
                    uid=account_details["uid"],
                    nickname=account_details["nickname"],
                    rank=account_details["rank"],
                    region=account_details["region"]
                )
        except Exception as e:
            logger.error(f"Error updating account details: {e}")

    async def get_account_id(self, account_name: str, game_name: str) -> Optional[int]:
        """Get account ID from database - simplified for now"""
        # This is a simplified implementation
        # In a real scenario, you'd need guild_id context
        try:
            # For now, we'll implement this later when we have guild context
            # This method needs to be enhanced with proper guild/user context
            return None
        except Exception as e:
            logger.error(f"Error getting account ID: {e}")
            return None

    def __del__(self):
        """Cleanup session on destruction"""
        if hasattr(self, 'session'):
            self.session.close()