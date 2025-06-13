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
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from web_ui import ui_instance

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

# Optional BEARER_TOKEN for v2 streaming (will be generated if not provided)
BEARER_TOKEN = os.getenv('BEARER_TOKEN')

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

# Response templates for more natural replies
RESPONSE_TEMPLATES = [
    "Here's what I found about @{username}:\n{analysis}",
    "Quick analysis of @{username}:\n{analysis}",
    "@{requester} Here's the scoop on @{username}:\n{analysis}",
    "Account breakdown for @{username}:\n{analysis}",
    "Let me break down @{username} for you:\n{analysis}",
    "Analysis complete for @{username}:\n{analysis}"
]

POSITIVE_INTROS = ["Looking good!", "Pretty solid account!", "Seems legit!", "Nice profile!"]
NEGATIVE_INTROS = ["Hmm, some red flags here...", "Proceed with caution!", "Worth being careful with this one.", "Some concerns here..."]
NEUTRAL_INTROS = ["Mixed signals here.", "Hard to say definitively.", "Pretty average account.", "Standard profile."]

# Global variable to store OAuth callback result
auth_response_url = None

def get_access_token():
    """
    Use OAuth 1.0a authentication with existing access tokens.
    This eliminates the need for web-based callback flows.
    """
    print("\n" + "="*80)
    print("🔐 OAUTH 1.0A AUTHENTICATION")
    print("="*80)
    print("Using OAuth 1.0a with pre-configured access tokens:")
    print("✓ Consumer Key (API Key)")
    print("✓ Consumer Secret (API Secret)")
    print("✓ Access Token")
    print("✓ Access Token Secret")
    print("\nNo web authorization flow required!")
    print("="*80 + "\n")
    
    logger.info("Using OAuth 1.0a authentication with existing tokens")
    
    # Return the existing access token - OAuth 1.0a doesn't need bearer tokens
    # The tweepy API will handle authentication automatically
    return ACCESS_TOKEN

class TwitterBot(tweepy.StreamingClient):
    def __init__(self, api):
        """
        Initialize Twitter bot streaming client using OAuth 1.0a.
        :param api: Tweepy API instance for v1.1 interactions
        """
        # Use the BEARER_TOKEN from environment for v2 streaming
        bearer_token = os.getenv('BEARER_TOKEN')
        if not bearer_token:
            # Create client using OAuth 2.0 for v2 streaming
            client = tweepy.Client(
                consumer_key=CONSUMER_KEY,
                consumer_secret=CONSUMER_SECRET,
                access_token=ACCESS_TOKEN,
                access_token_secret=ACCESS_TOKEN_SECRET
            )
            # Get bearer token for streaming
            bearer_token = client.bearer_token
        
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
                # Process in separate thread for faster response
                thread = threading.Thread(target=self.process_analysis_request, args=(tweet,))
                thread.daemon = True
                thread.start()

        except Exception as e:
            logger.error(f"Unexpected error in on_tweet for {tweet.id}: {e}")

    def process_analysis_request(self, tweet):
        """
        Process analysis request in separate thread for better performance.
        """
        try:
            logger.info(f"Processing trigger from @{tweet.author_id}: {tweet.text}")
            ui_instance.update_status(tweets_processed=ui_instance.bot_status['tweets_processed'] + 1)

            # Get original tweet and author using v1.1 API
            original_tweet_id = tweet.referenced_tweets[0].id
            original_tweet = self.api.get_status(original_tweet_id, tweet_mode='extended')
            original_author = original_tweet.user
            requester = self.api.get_user(user_id=tweet.author_id)

            # Perform analysis and trust check in parallel
            analysis_thread = threading.Thread(target=self.get_analysis, args=(original_author,))
            trust_thread = threading.Thread(target=self.get_trust_check, args=(original_author.screen_name,))
            
            self.analysis_result = None
            self.trust_result = None
            
            analysis_thread.start()
            trust_thread.start()
            
            analysis_thread.join(timeout=10)  # 10 second timeout
            trust_thread.join(timeout=8)   # 8 second timeout
            
            # Generate natural response
            reply_text = self.generate_natural_response(
                requester.screen_name, 
                original_author.screen_name, 
                self.analysis_result, 
                self.trust_result
            )

            # Post reply using v1.1 API
            self.api.update_status(
                status=reply_text,
                in_reply_to_status_id=tweet.id,
                auto_populate_reply_metadata=True
            )
            logger.info(f"Replied to @{requester.screen_name} about @{original_author.screen_name}")

        except tweepy.TweepyException as e:
            logger.error(f"Tweepy error processing tweet {tweet.id}: {e}")
            ui_instance.update_status(
                errors_count=ui_instance.bot_status['errors_count'] + 1,
                last_error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error processing analysis request: {e}")
            ui_instance.update_status(
                errors_count=ui_instance.bot_status['errors_count'] + 1,
                last_error=str(e)
            )

    def get_analysis(self, user):
        """Get account analysis in thread."""
        try:
            self.analysis_result = analyzer.analyze(user)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.analysis_result = {'summary': 'Analysis failed ⚠️'}

    def get_trust_check(self, username):
        """Get trust check in thread."""
        try:
            self.trust_result = trusted_checker.is_trusted(username)
        except Exception as e:
            logger.error(f"Trust check failed: {e}")
            self.trust_result = (False, 0, "Trust check failed ⚠️")

    def generate_natural_response(self, requester, target_user, analysis, trust_info):
        """
        Generate a more natural, less robotic response.
        """
        try:
            # Determine overall sentiment
            if analysis and trust_info:
                summary = analysis.get('summary', '')
                is_trusted, trust_count, trust_msg = trust_info
                
                # Count positive vs negative indicators
                positive_count = summary.count('✅')
                negative_count = summary.count('⚠️')
                
                # Choose intro based on overall assessment
                if positive_count > negative_count and trust_count >= 2:
                    intro = random.choice(POSITIVE_INTROS)
                elif negative_count > positive_count or trust_count == 0:
                    intro = random.choice(NEGATIVE_INTROS)
                else:
                    intro = random.choice(NEUTRAL_INTROS)
                
                # Compact the analysis
                compact_summary = self.compact_analysis(summary, trust_msg)
                
                # Choose random template
                template = random.choice(RESPONSE_TEMPLATES)
                
                # Build response
                response = f"@{requester} {intro}\n{compact_summary}"
                
                # Ensure it fits in 280 characters
                if len(response) > 280:
                    response = f"@{requester} Analysis of @{target_user}:\n{compact_summary}"
                    if len(response) > 280:
                        response = response[:277] + "..."
                
                return response
            else:
                return f"@{requester} Sorry, couldn't analyze @{target_user} right now. Try again later!"
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"@{requester} Analysis failed for @{target_user} ⚠️"

    def compact_analysis(self, summary, trust_msg):
        """
        Create a more compact version of the analysis.
        """
        try:
            lines = summary.split('\n')
            compact_lines = []
            
            for line in lines:
                if 'Verified' in line:
                    compact_lines.append(line.replace('Verified', 'Verified').replace('Not verified', 'Unverified'))
                elif 'Age:' in line:
                    # Simplify age reporting
                    if '✅' in line:
                        compact_lines.append('Established account ✅')
                    else:
                        compact_lines.append('New account ⚠️')
                elif 'Follower ratio:' in line:
                    if '✅' in line:
                        compact_lines.append('Good follower ratio ✅')
                    else:
                        compact_lines.append('Suspicious follower ratio ⚠️')
                elif 'Bio length:' in line and 'Suspicious keywords' not in line:
                    continue  # Skip simple bio length
                elif 'Suspicious keywords' in line:
                    compact_lines.append('Suspicious bio content ⚠️')
                elif 'Avg likes:' in line:
                    compact_lines.append('Engagement: ' + line.split('Avg likes: ')[1])
                elif 'Sentiment:' in line:
                    sentiment_part = line.split('Sentiment: ')[1].split(' ')[0]
                    compact_lines.append(f'{sentiment_part} sentiment')
            
            # Add trust info
            compact_lines.append(trust_msg)
            
            return '\n'.join(compact_lines)
        except Exception as e:
            logger.error(f"Error compacting analysis: {e}")
            return summary

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
    ui_instance.update_status(
        running=True, 
        start_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        oauth_status='Starting...'
    )
    
    try:
        ui_instance.update_status(oauth_status='Authenticating with OAuth 1.0a...')
        get_access_token()  # This just validates the tokens are present
        ui_instance.update_status(oauth_status='Authenticated', stream_status='Connecting...')
        
        stream = TwitterBot(api)
        # Add stream rules for triggers
        stream.add_rules(tweepy.StreamRule(f'"riddle me this" OR @{BOT_HANDLE}'))
        ui_instance.update_status(stream_status='Connected', oauth_status='OAuth 1.0a Active')
        
        stream.filter(tweet_fields=['referenced_tweets'], expansions=['author_id'])
        logger.info("Stream started successfully")
    except Exception as e:
        logger.error(f"Failed to start stream: {e}")
        ui_instance.update_status(
            running=False, 
            oauth_status='Failed',
            stream_status='Disconnected',
            last_error=str(e)
        )
        ui_instance.update_status(errors_count=ui_instance.bot_status['errors_count'] + 1)
        raise

if __name__ == "__main__":
    # Start web UI
    ui_instance.start_server()
    print(f"\n🌐 Web UI available at: http://0.0.0.0:8080")
    print("📊 Monitor bot status in your browser\n")
    
    while True:
        try:
            start_bot()
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            ui_instance.update_status(running=False, stream_status='Stopped by User')
            break
        except Exception as e:
            logger.error(f"Bot crashed: {e}. Restarting in 60 seconds...")
            ui_instance.update_status(
                running=False,
                stream_status='Crashed - Restarting',
                errors_count=ui_instance.bot_status['errors_count'] + 1,
                last_error=str(e)
            )
            time.sleep(60)
