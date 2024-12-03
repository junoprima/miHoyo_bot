import logging
import requests
from concurrent.futures import ThreadPoolExecutor
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the CONSTANTS_PATH environment variable
constants_path = os.getenv("CONSTANTS_PATH", "/app/constants.json")  # Default to /app/constants.json if not set

# Check if the file exists
if not os.path.isfile(constants_path):
    raise FileNotFoundError(f"Constants file not found at: {constants_path}")

print(f"Using constants file at: {constants_path}")

# Load the constants file
with open(constants_path, "r") as file:
    constants = file.read()  # Replace with actual loading logic

class Game:
    def __init__(self, name, config, cookies):
        self.name = name
        self.full_name = config["game"]
        self.config = config
        self.data = cookies  # Directly assign cookies since it's already a list
        self.session = requests.Session()  # Reuse session for persistent connections
        self.awards = None

        if not self.data:
            logging.warning(f"No {self.full_name} accounts provided. Skipping...")

    def process_account(self, account):
        try:
            if not isinstance(account, dict):
                raise ValueError("Account data should be a dictionary.")

            name = account.get("name", "Unknown")
            cookie = account.get("cookie")
            if not cookie:
                raise ValueError("Missing 'cookie' field in account data.")

            logging.info(f"Processing account: {name} for {self.full_name}")

            sign_info = self.get_sign_info(account["cookie"])
            if not sign_info["success"]:
                logging.warning(f"{name}: Failed to retrieve sign info. Reason: {sign_info.get('message', 'Unknown error')}")
                return None

            if sign_info["data"]["is_signed"]:
                logging.info(f"{name}: Already signed in today.")
                return None

            ltuid = self.extract_ltuid(cookie)
            account_details = self.get_account_details(cookie, ltuid)
            if not account_details:
                logging.warning(f"{name}: Failed to retrieve account details.")
                return None

            if not self.awards:
                self.awards = self.get_awards_data(cookie)["data"]

            total_signed = sign_info["data"]["total"]
            award_object = {
                "name": self.awards[total_signed]["name"],
                "count": self.awards[total_signed]["cnt"],
                "icon": self.awards[total_signed]["icon"],
            }

            sign = self.sign(cookie)
            if not sign["success"]:
                logging.warning(f"{name}: Failed to sign in.")
                return None

            logging.info(
                f"{name}: Successfully signed in. Today's reward: {award_object['name']} x{award_object['count']}"
            )
            return {
                "platform": self.name,
                "total": sign_info["data"]["total"] + 1,
                "result": self.config["successMessage"],
                "assets": self.config["assets"],
                "account": account_details,
                "award": award_object,
                "name": name,
            }
        except Exception as e:
            logging.error(f"{self.full_name}: Error processing account: {e}")
            return None

    def check_and_execute(self):
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
        return next(
            (item.split("=")[1] for item in cookie.split(";") if "ltuid_v2" in item),
            None,
        )

    def get_account_details(self, cookie, ltuid):
        try:
            url = f"https://bbs-api-os.hoyolab.com/game_record/card/wapi/getGameRecordCard?uid={ltuid}"
            headers = {"User-Agent": self.user_agent, "Cookie": cookie}
            response = self.session.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data["retcode"] != 0:
                raise ValueError(f"Failed to login: {data}")

            account_data = next(
                (acc for acc in data["data"]["list"] if acc["game_id"] == self.config["gameId"]), None
            )
            if not account_data:
                raise ValueError(f"No {self.full_name} account found for ltuid: {ltuid}")

            return {
                "uid": account_data["game_role_id"],
                "nickname": account_data["nickname"],
                "rank": account_data["level"],
                "region": self.fix_region(account_data["region"]),
            }
        except Exception as e:
            logging.error(f"{self.full_name}: Error fetching account details: {e}")
            return None

    def get_sign_info(self, cookie):
        try:
            url = f"{self.config['url']['info']}?act_id={self.config['ACT_ID']}"
            headers = {"Cookie": cookie, "x-rpc-signgame": self.get_sign_game_header()}
            response = self.session.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data["retcode"] != 0:
                logging.warning(f"{self.full_name}: Error getting sign info. Retcode: {data['retcode']}, Message: {data['message']}")
                return {"success": False, "message": data['message']}

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
        try:
            url = f"{self.config['url']['home']}?act_id={self.config['ACT_ID']}"
            headers = {"Cookie": cookie, "x-rpc-signgame": self.get_sign_game_header()}
            response = self.session.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data["retcode"] != 0:
                logging.warning(f"{self.full_name}: Error getting awards data: {data}")
                return {"success": False}

            return {"success": True, "data": data["data"]["awards"]}
        except Exception as e:
            logging.error(f"{self.full_name}: Error getting awards data: {e}")
            return {"success": False}

    def sign(self, cookie):
        try:
            url = self.config["url"]["sign"]
            payload = {"act_id": self.config["ACT_ID"]}
            headers = {
                "User-Agent": self.user_agent,
                "Cookie": cookie,
                "Content-Type": "application/json",
            }
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data["retcode"] != 0:
                logging.warning(f"{self.full_name}: Error signing in: {data}")
                return {"success": False}

            return {"success": True}
        except Exception as e:
            logging.error(f"{self.full_name}: Error signing in: {e}")
            return {"success": False}

    def get_sign_game_header(self):
        headers = {
            "starrail": "hkrpg",
            "genshin": "hk4e",
            "zenless": "zzz",
        }
        return headers.get(self.name, "")

    def fix_region(self, region):
        region_map = {
            "os_cht": "TW",
            "os_asia": "SEA",
            "os_euro": "EU",
            "os_usa": "NA",
        }
        return region_map.get(region, "Unknown")

    @property
    def user_agent(self):
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/110.0.0.0 Safari/537.36"
        )
