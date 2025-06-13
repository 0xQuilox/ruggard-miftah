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

            # Check cache first
            if hasattr(self, 'trust_cache'):
                cache_key = target_handle
                current_time = datetime.now()
                if cache_key in self.trust_cache:
                    cached_result, cache_time = self.trust_cache[cache_key]
                    if current_time - cache_time < timedelta(hours=1):  # 1 hour cache
                        return cached_result
            else:
                self.trust_cache = {}

            trusted_count = 0
            checked_count = 0
            max_checks = 30  # Reduced for speed

            for trusted_handle in self.trusted_handles[:max_checks]:
                try:
                    # Check if trusted account follows target
                    friendship = self.api.get_friendship(
                        source_screen_name=trusted_handle,
                        target_screen_name=target_handle
                    )[0]
                    if friendship.following:
                        trusted_count += 1

                    checked_count += 1

                    # Early exit if we have enough evidence
                    if trusted_count >= 3:
                        break

                    # Also break early if we've checked enough without finding trust
                    if checked_count >= 15 and trusted_count == 0:
                        break

                except tweepy.errors.TweepyException as e:
                    logger.warning(f"Error checking friendship for {trusted_handle}: {e}")
                    continue

            # Generate message
            if trusted_count >= 3:
                message = f"Highly trusted ({trusted_count}+ follows) ✅"
                is_trusted = True
            elif trusted_count >= 2:
                message = f"Trusted ({trusted_count} follows) ✅"
                is_trusted = True
            elif trusted_count == 1:
                message = f"Some trust (1 follow) ⚠️"
                is_trusted = False
            else:
                message = "No trusted follows ⚠️"
                is_trusted = False

            result = (is_trusted, trusted_count, message)

            # Cache the result
            self.trust_cache[target_handle] = (result, datetime.now())

            # Clean old cache entries
            if len(self.trust_cache) > 100:
                oldest_key = min(self.trust_cache.keys(), 
                               key=lambda k: self.trust_cache[k][1])
                del self.trust_cache[oldest_key]

            logger.info(f"{target_handle} trusted check: {message}")
            return result

        except Exception as e:
            logger.error(f"Unexpected error in is_trusted for {target_handle}: {e}")
            return False, 0, "Trust check failed ⚠️"