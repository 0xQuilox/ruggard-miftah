import tweepy
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
from trusted_accounts import TrustedAccounts
from account_analysis import AccountAnalyzer
import time
import re

# Configure logging with rotation
from logging.handlers import RotatingFileHandler

log_handler = RotatingFileHandler('bot.log', maxBytes=5*1024*1024, backupCount=5)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        log_handler,
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Twitter API credentials
CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
BOT_HANDLE = os.getenv('BOT_HANDLE', 'YourBotHandle').lower()

# Validate environment variables
required_env_vars = ['CONSUMER_KEY', 'CONSUMER_SECRET', 'ACCESS_TOKEN', 'ACCESS_TOKEN_SECRET']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
    raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")

# Initialize Twitter API
try:
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    logger.info("Twitter API initialized successfully")
except tweepy.errors.TweepyException as e:
    logger.error(f"Failed to initialize Twitter API: {e}")
    raise

# Initialize analyzers
analyzer = AccountAnalyzer(api)
trusted_checker = TrustedAccounts(api)

class TwitterBot(tweepy.StreamListener):
    def __init__(self, api):
        """
        Initialize Twitter bot stream listener.
        :param api: Tweepy API instance
        """
        super().__init__()
        self.api = api

    def on_status(self, status):
        """
        Handle incoming tweets.
        :param status: Tweepy Status object
        """
        try:
            # Skip if tweet is from the bot itself
            if status.user.screen_name.lower() == BOT_HANDLE:
                return

            # Check if tweet is a reply or mentions the bot
            is_reply = status.in_reply_to_status_id is not None
            text = status.text.lower() if status.text else ''
            mentions_bot = f'@{BOT_HANDLE}' in text
            contains_trigger = 'riddle me this' in text

            if is_reply and (contains_trigger or mentions_bot):
                logger.info(f"Processing trigger from @{status.user.screen_name}: {status.text}")

                # Get original tweet and author
                original_tweet = self.api.get_status(
                    status.in_reply_to_status_id,
                    tweet_mode='extended'
                )
                original_author = original_tweet.user

                # Perform account analysis
                analysis = analyzer.analyze(original_author)

                # Perform trusted accounts check
                is_trusted, trusted_count, trusted_message = trusted_checker.is_trusted(original_author.screen_name)

                # Compile reply
                summary = analysis.get('summary', 'Analysis unavailable ⚠️')
                if is_trusted:
                    summary += f"\n{trusted_message}"
                else:
                    summary += f"\n{trusted_message}"

                # Ensure reply is within 280 characters
                reply_prefix = f"@{status.user.screen_name} Trustworthiness of @{original_author.screen_name}:\n"
                max_summary_length = 280 - len(reply_prefix) - 3  # Buffer for ellipsis
                if len(summary) > max_summary_length:
                    summary = summary[:max_summary_length - 3] + "..."

                reply_text = reply_prefix + summary

                # Post reply
                self.api.update_status(
                    status=reply_text,
                    in_reply_to_status_id=status.id,
                    auto_populate_reply_metadata=True
                )
                logger.info(f"Replied to @{status.user.screen_name} about @{original_author.screen_name}")

        except tweepy.errors.TweepyException as e:
            logger.error(f"Tweepy error processing status {status.id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing status {status.id}: {e}")

    def on_error(self, status_code):
        """
        Handle stream errors.
        :param status_code: HTTP status code
        :return: False to disconnect on rate limit
        """
        logger.error(f"Stream error: {status_code}")
        if status_code == 420:  # Rate limit
            return False
        return True

def start_bot():
    """
    Start the Twitter bot stream.
    """
    logger.info("Starting Twitter bot...")
    stream_listener = TwitterBot(api)
    stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
    
    try:
        stream.filter(track=['riddle me this', f'@{BOT_HANDLE}'], is_async=True)
        logger.info("Stream started successfully")
    except Exception as e:
        logger.error(f"Failed to start stream: {e}")
        raise

if __name__ == "__main__":
    while True:
        try:
            start_bot()
            # Keep the script running
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Bot crashed: {e}. Restarting in 60 seconds...")
            time.sleep(60)