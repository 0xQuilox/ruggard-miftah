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
oauth_tokens = {}

def get_access_token():
    """
    Get access token using OAuth 2.0 flow.
    Returns access token for API usage.
    """
    print("\n" + "="*80)
    print("🔐 OAUTH 2.0 AUTHENTICATION")
    print("="*80)
    
    try:
        # Create OAuth 2.0 handler - use root path for callback
        repl_url = os.getenv('REPL_URL', 'https://ruggard.replit.app/auth/twitter/callback')
        callback_url = f"{repl_url}/"  # Use root path as callback
        
        oauth2_user_handler = tweepy.OAuth2UserHandler(
            client_id=CLIENT_ID,
            redirect_uri=callback_url,
            scope=["tweet.read", "tweet.write", "users.read", "follows.read"],
            client_secret=CLIENT_SECRET
        )
        
        # Get authorization URL
        authorization_url = oauth2_user_handler.get_authorization_url()
        
        print(f"🔗 Please visit this URL to authorize the application:")
        print(f"🌐 {authorization_url}")
        print("="*80 + "\n")
        
        logger.info(f"OAuth authorization URL generated: {authorization_url}")
        return authorization_url
        
    except Exception as e:
        logger.error(f"Failed to generate OAuth URL: {e}")
        return None

class TwitterBot(tweepy.StreamingClient):
    def __init__(self, bearer_token, api_client):
        """
        Initialize Twitter bot streaming client using OAuth 2.0.
        :param bearer_token: Bearer token for v2 streaming
        :param api_client: Tweepy Client instance for v2 interactions
        """
        super().__init__(bearer_token)
        self.client = api_client

    def on_tweet(self, tweet):
        """
        Handle incoming tweets.
        :param tweet: Tweepy Tweet object (API v2)
        """
        try:
            # Skip if tweet is from the bot itself
            bot_user = self.client.get_me().data
            if tweet.author_id == bot_user.id:
                return

            # Check if tweet is a reply or mentions the bot
            is_reply = tweet.referenced_tweets and any(ref.type == 'replied_to' for ref in tweet.referenced_tweets)
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

            # Get original tweet and author using v2 API
            original_tweet_id = next(ref.id for ref in tweet.referenced_tweets if ref.type == 'replied_to')
            original_tweet = self.client.get_tweet(original_tweet_id, expansions=['author_id'])
            original_author = self.client.get_user(id=original_tweet.data.author_id)
            requester = self.client.get_user(id=tweet.author_id)

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

            # Post reply using v2 API
            self.client.create_tweet(
                text=reply_text,
                in_reply_to_tweet_id=tweet.id
            )
            logger.info(f"Replied to @{requester.data.username} about @{original_author.data.username}")

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
    Start the Twitter bot stream using OAuth 2.0.
    """
    logger.info("Starting Twitter bot...")
    ui_instance.update_status(
        running=True, 
        start_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        oauth_status='Starting OAuth 2.0...'
    )
    
    try:
        # Step 1: Generate OAuth URL
        ui_instance.update_status(oauth_status='Generating OAuth URL...')
        auth_url = get_access_token()
        
        if not auth_url:
            raise Exception("Failed to generate OAuth authorization URL")
        
        ui_instance.update_status(oauth_status='Waiting for OAuth callback...')
        
        # Step 2: Wait for OAuth callback
        max_wait = 300  # 5 minutes
        wait_count = 0
        while 'access_token' not in oauth_tokens and wait_count < max_wait:
            time.sleep(1)
            wait_count += 1
        
        if 'access_token' not in oauth_tokens:
            raise Exception("OAuth authentication timeout - no callback received")
        
        # Step 3: Create authenticated client
        ui_instance.update_status(oauth_status='Creating authenticated client...')
        
        # Use OAuth 2.0 client
        client = tweepy.Client(
            bearer_token=BEARER_TOKEN,
            access_token=oauth_tokens['access_token']['access_token']
        )
        
        ui_instance.update_status(oauth_status='Authenticated', stream_status='Connecting...')
        
        # Step 4: Start streaming
        stream = TwitterBot(BEARER_TOKEN, client)
        stream.add_rules(tweepy.StreamRule(f'"riddle me this" OR @{BOT_HANDLE}'))
        ui_instance.update_status(stream_status='Connected', oauth_status='OAuth 2.0 Active')
        
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
