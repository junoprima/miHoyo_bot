import logging
import requests
import json
import os
import time
from dotenv import load_dotenv
from utils.discord import send_discord_notification

# Load environment variables
load_dotenv()

# Get the CONSTANTS_PATH environment variable
constants_path = os.getenv("CONSTANTS_PATH", "constants.json")  # Default to constants.json if not set

# Helper function to load constants
def load_constants(file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Constants file not found at: {file_path}")
    with open(file_path, "r") as file:
        return json.load(file)

# Load the constants
constants = load_constants(constants_path)
print(f"Using constants file at: {constants_path}")


class Game:
    def __init__(self, name, config, cookies):
        self.name = name
        self.full_name = config["game"]
        self.config = config
        self.data = cookies
        self.session = requests.Session()  # Reuse session for persistent connections
        self.awards = None

        if not self.data:
            logging.warning(f"No {self.full_name} accounts provided. Skipping...")

    def sign(self, cookie, retries=2):
        """Sign in to the game with retry logic."""
        for attempt in range(1, retries + 1):
            try:
                url = self.config["url"]["sign"]
                payload = {"act_id": self.config["ACT_ID"]}
                headers = {
                    "User-Agent": self.user_agent,
                    "Cookie": cookie,
                    "Content-Type": "application/json",
                    "x-rpc-signgame": self.get_sign_game_header(),
                    "x-rpc-client_type": "5",
                    "x-rpc-app_version": "2.34.1",
                }

                logging.debug(f"Attempt {attempt}: Sign request payload: {payload}")
                response = self.session.post(url, json=payload, headers=headers)
                response.raise_for_status()

                data = response.json()
                logging.debug(f"Attempt {attempt}: Sign response: {data}")

                if data["retcode"] == -500012:
                    logging.warning(f"{self.full_name}: Event may be temporarily unavailable. Retrying...")
                    time.sleep(5)  # Wait before retrying
                    continue

                if data["retcode"] != 0:
                    logging.warning(f"{self.full_name}: Error signing in. Response: {data}")
                    return {"success": False, "message": data.get("message", "Unknown error")}

                logging.info(f"{self.full_name}: Successfully signed in!")
                return {"success": True}

            except Exception as e:
                logging.error(f"{self.full_name}: Error signing in on attempt {attempt}: {e}")
                if attempt == retries:
                    return {"success": False, "message": str(e)}

    def process_account(self, account):
        try:
            if not isinstance(account, dict):
                raise ValueError("Account data should be a dictionary.")

            # Fetch and validate the cookie
            cookie = account.get("cookie")
            if not cookie:
                raise ValueError(f"Missing 'cookie' field in account data: {account}")

            # Log the cookie for debugging
            logging.debug(f"Cookie used for {self.full_name}: {cookie}")

            name = account.get("name", "Unknown")
            logging.info(f"Processing account: {name} for {self.full_name}")

            # Fetch sign info
            sign_info = self.get_sign_info(cookie)
            if not sign_info["success"]:
                logging.warning(f"{name}: Failed to retrieve sign info. Reason: {sign_info.get('message', 'Unknown error')}")
                return None

            # Check if already signed in
            if sign_info["data"]["is_signed"]:
                logging.info(f"{name}: Already signed in today.")
                return None

            # Fetch account details
            ltuid = self.extract_ltuid(cookie)
            if not ltuid:
                logging.warning(f"{name}: ltuid_v2 is missing or invalid in the cookie.")
                return None

            account_details = self.get_account_details(cookie, ltuid)
            if not account_details:
                logging.warning(f"{name}: Failed to retrieve account details.")
                return None

            # Fetch awards data if not already loaded
            if not self.awards:
                awards_data = self.get_awards_data(cookie)
                if not awards_data["success"]:
                    logging.warning(f"{name}: Failed to fetch awards data.")
                    return None
                self.awards = awards_data["data"]

            # Determine today's reward
            total_signed = sign_info["data"]["total"]
            award_object = {
                "name": self.awards[total_signed]["name"],
                "count": self.awards[total_signed]["cnt"],
                "icon": self.awards[total_signed]["icon"],
            }

            # Attempt to sign in
            sign_response = self.sign(cookie)
            if not sign_response["success"]:
                logging.warning(f"{name}: Failed to sign in. Reason: {sign_response.get('message', 'Unknown error')}")
                return None

            # Log success
            logging.info(
                f"{name}: Successfully signed in. Today's reward: {award_object['name']} x{award_object['count']}"
            )

            # Prepare success data
            success_data = {
                "platform": self.name,
                "total": sign_info["data"]["total"] + 1,
                "result": self.config["successMessage"],
                "assets": self.config["assets"],
                "account": account_details,
                "award": award_object,
                "name": name,
            }

            # Send Discord notification
            send_discord_notification(success_data)

            return success_data
        except Exception as e:
            logging.error(f"{self.full_name}: Error processing account: {e}")
            return None

    def check_and_execute(self):
        """Process all accounts for the current game."""
        if not self.data:
            logging.warning(f"No active accounts found for {self.full_name}")
            return []

        successes = []
        for account in self.data:
            result = self.process_account(account)
            if result:
                successes.append(result)

        logging.info(f"{self.full_name}: All accounts processed.")
        return successes

    def extract_ltuid(self, cookie):
        """Extract ltuid_v2 from the cookie."""
        ltuid = next(
            (item.split("=")[1] for item in cookie.split(";") if "ltuid_v2" in item),
            None,
        )
        logging.debug(f"Extracted ltuid_v2 for {self.full_name}: {ltuid}")
        if not ltuid:
            logging.warning(f"{self.full_name}: ltuid_v2 is missing from the cookie!")
        return ltuid

    def get_account_details(self, cookie, ltuid):
        """Retrieve account details for the given cookie and ltuid."""
        try:
            url = f"https://bbs-api-os.hoyolab.com/game_record/card/wapi/getGameRecordCard?uid={ltuid}"
            headers = {"User-Agent": self.user_agent, "Cookie": cookie}
            logging.debug(f"Fetching account details for {self.full_name} with URL: {url}")
            response = self.session.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            logging.debug(f"Account details response: {data}")

            if data["retcode"] != 0:
                logging.warning(f"{self.full_name}: Error fetching account details. Retcode: {data['retcode']}, Message: {data['message']}")
                return None

            # Extract account details for the specific game ID
            account_data = next(
                (acc for acc in data["data"]["list"] if acc["game_id"] == self.config["gameId"]), None
            )
            if not account_data:
                logging.warning(f"{self.full_name}: No account data found for game_id: {self.config['gameId']}.")
                return None

            return {
                "uid": account_data["game_role_id"],
                "nickname": account_data["nickname"],
                "rank": account_data["level"],
                "region": self.fix_region(account_data["region"]),
            }
        except Exception as e:
            logging.error(f"{self.full_name}: Error fetching account details: {e}")
            return None
        
    def fix_region(self, region):
        """Map internal region identifiers to readable names."""
        region_map = {
            # Common regions for Hoyoverse games
            "os_cht": "TW",
            "os_asia": "SEA",
            "os_euro": "EU",
            "os_usa": "NA",
            # Specific mappings for Honkai Star Rail
            "prod_official_asia": "SEA",
            "prod_official_usa": "NA",
            "prod_official_eur": "EU",
            "prod_official_cht": "TW",
        }
        return region_map.get(region, "Unknown")

    def get_sign_info(self, cookie):
        """Retrieve sign-in info for the account."""
        try:
            url = f"{self.config['url']['info']}?act_id={self.config['ACT_ID']}"
            headers = {"Cookie": cookie, "x-rpc-signgame": self.get_sign_game_header()}
            logging.debug(f"Sign info request URL: {url}")
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data["retcode"] != 0:
                logging.warning(f"{self.full_name}: Error getting sign info. Response: {data}")
                return {"success": False, "message": data["message"]}

            return {
                "success": True,
                "data": {
                    "total": data["data"]["total_sign_day"],
                    "today": data["data"]["today"],
                    "is_signed": data["data"]["is_sign"],
                },
            }
        except Exception as e:
            logging.error(f"{self.full_name}: Error getting sign info: {e}")
            return {"success": False, "message": str(e)}

    def get_awards_data(self, cookie):
        """Retrieve awards data for the account."""
        try:
            url = f"{self.config['url']['home']}?act_id={self.config['ACT_ID']}"
            headers = {
                "Cookie": cookie,
                "x-rpc-signgame": self.get_sign_game_header(),
                "User-Agent": self.user_agent,
            }

            logging.debug(f"Awards data request URL: {url}")
            logging.debug(f"Awards data request headers: {headers}")

            response = self.session.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            logging.debug(f"Awards data response: {data}")

            if data["retcode"] != 0:
                logging.warning(
                    f"{self.full_name}: Error getting awards data. Retcode: {data['retcode']}, Message: {data['message']}"
                )
                return {"success": False}

            if not data.get("data", {}).get("awards"):
                logging.warning(f"{self.full_name}: No awards data found.")
                return {"success": False, "data": []}

            return {"success": True, "data": data["data"]["awards"]}
        except Exception as e:
            logging.error(f"{self.full_name}: Error getting awards data: {e}")
            return {"success": False, "data": []}

    def get_sign_game_header(self):
        """Return the x-rpc-signgame header based on the game configuration."""
        header = self.config.get("signGameHeader")
        if not header:
            logging.warning(f"{self.full_name}: Missing 'signGameHeader' configuration. Falling back to default.")
            header = "default-header"  # Replace with an appropriate fallback value
        return header


    @property
    def user_agent(self):
        """Return a standard user agent."""
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/110.0.0.0 Safari/537.36"
        )
