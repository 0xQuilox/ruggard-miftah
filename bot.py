import tweepy
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
from trusted_accounts import TrustedAccounts
from account_analysis import AccountAnalyzer
import time
import re
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

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
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
BOT_HANDLE = os.getenv('BOT_HANDLE', 'RuggardBot').lower()

# Validate environment variables
required_env_vars = ['CONSUMER_KEY', 'CONSUMER_SECRET', 'ACCESS_TOKEN', 'ACCESS_TOKEN_SECRET', 'CLIENT_ID', 'CLIENT_SECRET']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
    raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")

# Initialize Twitter API v1.1 for posting and analysis
try:
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    logger.info("Twitter API v1.1 initialized successfully")
except tweepy.TweepyException as e:
    logger.error(f"Failed to initialize Twitter API v1.1: {e}")
    raise

# Initialize analyzers
analyzer = AccountAnalyzer(api)
trusted_checker = TrustedAccounts(api)

# OAuth 2.0 authentication
class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        logger.info(f"Received request for path: {self.path}")
        if self.path.startswith('/auth/twitter/callback'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Authentication successful!</h2><p>You can close this window and return to the console.</p></body></html>")
            global auth_response_url
            auth_response_url = self.path
            logger.info("OAuth callback received successfully")
        else:
            logger.warning(f"Unexpected request path: {self.path}")
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Not Found</h2><p>Expected /auth/twitter/callback</p></body></html>")
    
    def log_message(self, format, *args):
        # Suppress default HTTP server logging to avoid clutter
        pass

def get_access_token():
    """
    Perform OAuth 2.0 authentication and return access token.
    """
    # Use the correct Replit URL format - get from environment or use default
    replit_url = os.getenv('REPL_URL', 'https://ruggard.replit.app')
    callback_url = f"{replit_url}/auth/twitter/callback"
    
    oauth2_user_handler = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        redirect_uri=callback_url,
        scope=['tweet.read', 'tweet.write', 'users.read', 'offline.access'],
        client_secret=CLIENT_SECRET
    )

    # Generate authorization URL
    auth_url = oauth2_user_handler.get_authorization_url()
    
    print("\n" + "="*80)
    print("🔐 AUTHORIZATION REQUIRED")
    print("="*80)
    print("Please visit this URL to authorize the bot:")
    print(f"\n{auth_url}\n")
    print("After authorization, return to this console.")
    print(f"Make sure your Twitter app callback URL is set to: {callback_url}")
    print("="*80 + "\n")
    
    logger.info(f"Authorization URL generated: {auth_url}")
    logger.info(f"Callback URL: {callback_url}")

    # Start local server to capture callback on port 5000
    global auth_response_url
    auth_response_url = None
    server = HTTPServer(('0.0.0.0', 5000), OAuthCallbackHandler)
    logger.info("Waiting for OAuth callback on port 5000...")
    server.handle_request()
    server.server_close()

    if auth_response_url:
        # Extract authorization response URL
        access_token = oauth2_user_handler.fetch_token(auth_response_url)
        logger.info("OAuth 2.0 access token obtained")
        return access_token['access_token']
    else:
        logger.error("Failed to receive OAuth callback")
        raise Exception("OAuth 2.0 authentication failed")

class TwitterBot(tweepy.StreamingClient):
    def __init__(self, bearer_token, api):
        """
        Initialize Twitter bot streaming client.
        :param bearer_token: Access token from OAuth 2.0
        :param api: Tweepy API instance for v1.1 interactions
        """
        super().__init__(bearer_token)
        self.api = api

    def on_tweet(self, tweet):
        """
        Handle incoming tweets.
        :param tweet: Tweepy Tweet object (API v2)
        """
        try:
            # Skip if tweet is from the bot itself
            if tweet.author_id == self.api.get_user(screen_name=BOT_HANDLE).id:
                return

            # Check if tweet is a reply or mentions the bot
            is_reply = tweet.referenced_tweets and tweet.referenced_tweets[0].type == 'replied_to'
            text = tweet.text.lower() if tweet.text else ''
            mentions_bot = f'@{BOT_HANDLE}' in text
            contains_trigger = 'riddle me this' in text

            if is_reply and (contains_trigger or mentions_bot):
                logger.info(f"Processing trigger from @{tweet.author_id}: {tweet.text}")

                # Get original tweet and author using v1.1 API
                original_tweet_id = tweet.referenced_tweets[0].id
                original_tweet = self.api.get_status(original_tweet_id, tweet_mode='extended')
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
                reply_prefix = f"@{self.api.get_user(user_id=tweet.author_id).screen_name} Trustworthiness of @{original_author.screen_name}:\n"
                max_summary_length = 280 - len(reply_prefix) - 3
                if len(summary) > max_summary_length:
                    summary = summary[:max_summary_length - 3] + "..."

                reply_text = reply_prefix + summary

                # Post reply using v1.1 API
                self.api.update_status(
                    status=reply_text,
                    in_reply_to_status_id=tweet.id,
                    auto_populate_reply_metadata=True
                )
                logger.info(f"Replied to @{tweet.author_id} about @{original_author.screen_name}")

        except tweepy.TweepyException as e:
            logger.error(f"Tweepy error processing tweet {tweet.id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing tweet {tweet.id}: {e}")

    def on_error(self, status):
        """
        Handle stream errors.
        :param status: Error status code
        """
        logger.error(f"Stream error: {status}")
        if status == 420:  # Rate limit
            return False
        return True

def start_bot():
    """
    Start the Twitter bot stream.
    """
    logger.info("Starting Twitter bot...")
    try:
        access_token = get_access_token()
        stream = TwitterBot(access_token, api)
        # Add stream rules for triggers
        stream.add_rules(tweepy.StreamRule(f'"riddle me this" OR @{BOT_HANDLE}'))
        stream.filter(tweet_fields=['referenced_tweets'], expansions=['author_id'])
        logger.info("Stream started successfully")
    except Exception as e:
        logger.error(f"Failed to start stream: {e}")
        raise

if __name__ == "__main__":
    while True:
        try:
            start_bot()
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Bot crashed: {e}. Restarting in 60 seconds...")
            time.sleep(60)
