import os
import sys
import io
import json
import time
import logging
from utils.firestore import fetch_cookies_from_firestore
from games.game import Game
from utils.logger import setup_logging
from dotenv import load_dotenv

# Set up encoding for stdout and stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()

# Load constants.json dynamically
CONSTANTS_FILE = os.getenv("CONSTANTS", "constants.json")
with open(CONSTANTS_FILE, "r") as file:
    DEFAULT_CONSTANTS = json.load(file)


def check_in_all_games():
    """Fetch configuration from Firestore and execute check-ins."""
    logging.info("----------------------------------------")
    logging.info("Starting Daily Check-in Process")
    logging.info("----------------------------------------")

    # Fetch cookies from Firestore
    cookies = fetch_cookies_from_firestore()
    if not cookies:
        logging.error("No account cookies retrieved from Firestore. Exiting...")
        return

    # Loop through all games in constants.json
    for game_name, config in DEFAULT_CONSTANTS.items():
        if game_name in cookies:
            logging.info(f"--------- {config['game']} ---------")
            game = Game(game_name, config, cookies[game_name])
            
            # Execute check-ins
            try:
                successes = game.check_and_execute()
                logging.info(f"{len(successes)} successful check-ins for {config['game']}.")
            except Exception as e:
                logging.error(f"Error during check-ins for {config['game']}: {e}")

    logging.info("----------------------------------------")
    logging.info(f"Check-in process completed in {time.time() - start_time:.2f} seconds.")
    logging.info("----------------------------------------")


if __name__ == "__main__":
    start_time = time.time()
    check_in_all_games()
