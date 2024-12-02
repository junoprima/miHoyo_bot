import os
import json
import time
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import requests

# Load environment variables
load_dotenv()
FIREBASE_KEY = os.getenv("FIREBASE_KEY")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

# Setup logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "log.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)

# Initialize Firebase
cred = credentials.Certificate(FIREBASE_KEY)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Load constants from a local file
with open("constants.json", "r") as file:
    DEFAULT_CONSTANTS = json.load(file)


class Game:
    def __init__(self, name, config):
        self.name = name
        self.full_name = DEFAULT_CONSTANTS[name]["game"]
        self.config = {**DEFAULT_CONSTANTS[name], **config.get("config", {})}
        self.data = config.get("data", [])
        self.session = requests.Session()  # Reuse session for persistent connections
        self.awards = None

        if not self.data:
            logging.warning(f"No {self.full_name} accounts provided. Skipping...")

    def process_account(self, account):
        try:
            name = account.get("name", "Unknown")
            cookie = account.get("cookie")
            logging.info(f"Processing account: {name} for {self.full_name}")

            sign_info = self.get_sign_info(cookie)
            if not sign_info["success"]:
                logging.warning(f"{name}: Failed to retrieve sign info.")
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
        with ThreadPoolExecutor() as executor:
            results = executor.map(self.process_account, self.data)
            successes = [result for result in results if result]

        for success in successes:
            send_discord_notification(success)

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
                logging.warning(f"{self.full_name}: Error getting sign info: {data}")
                return {"success": False}

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
            return {"success": False}

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

def fetch_config_from_firestore():
    """Fetch game configurations from Firestore."""
    configs = {}
    collection_ref = db.collection("gameConfigs")
    documents = collection_ref.stream()

    for doc in documents:
        configs[doc.id] = doc.to_dict()

    return configs


def send_discord_notification(success):
    embed = {
        "color": 16748258,
        "title": f"{success['assets']['game']} Daily Check-In",
        "author": {
            "name": success["name"],
            "icon_url": success["assets"]["icon"]
        },
        "fields": [
            {"name": "Nickname", "value": success["account"]["nickname"], "inline": True},
            {"name": "UID", "value": success["account"]["uid"], "inline": True},
            {"name": "Rank", "value": success["account"]["rank"], "inline": True},
            {"name": "Region", "value": success["account"]["region"], "inline": True},
            {
                "name": "Today's Reward",
                "value": f"{success['award']['name']} x{success['award']['count']}",
                "inline": True,
            },
            {"name": "Total Check-Ins", "value": success["total"], "inline": True},
            {"name": "Result", "value": success["result"], "inline": False},
        ],
        "thumbnail": {"url": success["award"]["icon"]},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": f"{success['assets']['game']} Daily Check-In"},
    }

    payload = {
        "embeds": [embed],
        "username": success["assets"]["author"],
        "avatar_url": success["assets"]["icon"],
    }

    try:
        response = requests.post(DISCORD_WEBHOOK, json=payload)
        response.raise_for_status()
        logging.info(f"Discord notification sent for {success['name']}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Discord notification: {e}")


def fetch_config_from_firestore():
    """Fetch game configurations from Firestore."""
    logging.info("Fetching game configurations from Firestore...")
    configs = {}
    collection_ref = db.collection("game_cookies")
    documents = collection_ref.stream()

    for doc in documents:
        logging.info(f"Retrieved document: {doc.id}")
        configs[doc.id] = doc.to_dict()

    logging.info("Game configurations fetched successfully.")
    return configs


def check_in_all_games():
    """Fetch configuration from Firestore and execute check-ins."""
    configs = fetch_config_from_firestore()
    if not configs:
        logging.error("No configurations retrieved from Firestore. Exiting...")
        return

    games = ["genshin", "honkai", "starrail", "zenless"]
    for game_name in games:
        if game_name in configs:
            logging.info(f"Starting check-in for {game_name}")
            game = Game(game_name, configs[game_name])
            game.check_and_execute()


if __name__ == "__main__":
    start_time = time.time()
    check_in_all_games()
    logging.info(f"Execution completed in {time.time() - start_time:.2f} seconds")