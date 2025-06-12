import requests
import json
import logging
from datetime import datetime, timedelta
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TrustedAccounts:
    def __init__(self, api, cache_file='trusted_list.json', cache_duration_hours=24):
        """
        Initialize trusted accounts module.
        :param api: Tweepy API instance for Twitter interactions
        :param cache_file: Local file to cache trusted list
        :param cache_duration_hours: Cache duration in hours
        """
        self.api = api
        self.cache_file = cache_file
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.trusted_handles = self.load_trusted_list()

    def load_trusted_list(self):
        """
        Load trusted accounts from cache or GitHub.
        :return: List of trusted Twitter handles
        """
        try:
            # Check if cache exists and is recent
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cache_time < self.cache_duration:
                    logger.info("Loaded trusted list from cache")
                    return cache_data['handles']

            # Fetch from GitHub
            url = 'https://raw.githubusercontent.com/devsyrem/turst-list/main/list'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Validate and extract handles
            handles = [entry['handle'].lower() for entry in data if 'handle' in entry]
            if not handles:
                logger.warning("No valid handles found in trusted list")
                return []

            # Cache the list
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'handles': handles
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info("Fetched and cached trusted list from GitHub")
            return handles

        except requests.RequestException as e:
            logger.error(f"Failed to fetch trusted list: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in trusted list: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in load_trusted_list: {e}")
            return []

    def is_trusted(self, target_handle):
        """
        Check if target user is followed by at least three trusted accounts.
        :param target_handle: Twitter handle to check (without @)
        :return: Tuple (is_trusted: bool, count: int, message: str)
        """
        try:
            target_handle = target_handle.lower().strip('@')
            if not target_handle or not target_handle.isalnum():
                logger.warning(f"Invalid target handle: {target_handle}")
                return False, 0, "Invalid handle"

            trusted_count = 0
            for trusted_handle in self.trusted_handles[:50]:  # Limit to avoid rate limits
                try:
                    # Check if trusted account follows target
                    friendship = self.api.get_friendship(
                        source_screen_name=trusted_handle,
                        target_screen_name=target_handle
                    )[0]
                    if friendship.following:
                        trusted_count += 1
                    if trusted_count >= 3:
                        logger.info(f"{target_handle} is followed by {trusted_count} trusted accounts")
                        return True, trusted_count, f"Followed by {trusted_count} trusted accounts ✅"
                except tweepy.errors.TweepyException as e:
                    logger.warning(f"Error checking friendship for {trusted_handle}: {e}")
                    continue

            message = f"Followed by {trusted_count} trusted account(s) {'✅' if trusted_count >= 2 else '⚠️'}"
            is_trusted = trusted_count >= 2
            logger.info(f"{target_handle} trusted check: {message}")
            return is_trusted, trusted_count, message

        except Exception as e:
            logger.error(f"Unexpected error in is_trusted for {target_handle}: {e}")
            return False, 0, "Trust check failed ⚠️"
