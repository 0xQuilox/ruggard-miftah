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

# OAuth 2.0 callback handler for Twitter authorization
class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        logger.info(f"OAuth callback received for path: {self.path}")
        
        # Check if this is the expected Twitter OAuth callback
        if self.path.startswith('/auth/twitter/callback') or '?code=' in self.path:
            # Validate that we received an authorization code
            if 'code=' in self.path:
                logger.info("✅ Authorization code received from Twitter")
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"""
                <html>
                    <head><title>Twitter OAuth Success</title></head>
                    <body style='font-family: Arial, sans-serif; text-align: center; padding: 50px;'>
                        <h2 style='color: #1DA1F2;'>✅ Twitter Authorization Successful!</h2>
                        <p>The bot has been authorized and is now processing your request.</p>
                        <p>You can safely close this window and return to the console.</p>
                        <p style='color: #666; font-size: 12px;'>OAuth 2.0 flow completed with PKCE verification</p>
                    </body>
                </html>
                """)
                global auth_response_url
                auth_response_url = self.path
                logger.info("OAuth 2.0 callback processed successfully")
            else:
                logger.warning("❌ No authorization code in callback")
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"""
                <html>
                    <head><title>OAuth Error</title></head>
                    <body style='font-family: Arial, sans-serif; text-align: center; padding: 50px;'>
                        <h2 style='color: #e74c3c;'>❌ Authorization Failed</h2>
                        <p>No authorization code received from Twitter.</p>
                        <p>Please try the authorization process again.</p>
                    </body>
                </html>
                """)
        else:
            logger.warning(f"Unexpected request path: {self.path}")
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <html>
                <head><title>Not Found</title></head>
                <body style='font-family: Arial, sans-serif; text-align: center; padding: 50px;'>
                    <h2>404 - Not Found</h2>
                    <p>Expected OAuth callback at /auth/twitter/callback</p>
                </body>
            </html>
            """)
    
    def log_message(self, format, *args):
        # Suppress default HTTP server logging to avoid clutter
        pass

def get_access_token():
    """
    Perform OAuth 2.0 authentication following the complete step-by-step flow:
    1. Generate Authorization URL with all required parameters
    2. Handle callback with authorization code
    3. Exchange code for access token using PKCE
    """
    # Use the correct Replit URL format - get from environment or use default
    replit_url = os.getenv('REPL_URL', 'https://ruggard.replit.app')
    callback_url = f"{replit_url}/auth/twitter/callback"
    
    # Initialize OAuth2UserHandler with proper PKCE implementation
    oauth2_user_handler = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        redirect_uri=callback_url,
        scope=['tweet.read', 'tweet.write', 'users.read', 'offline.access'],
        client_secret=CLIENT_SECRET
    )

    # Step 1: Generate Authorization URL with all required OAuth 2.0 parameters
    # This automatically includes:
    # - response_type=code
    # - client_id=<CLIENT_ID>
    # - redirect_uri=<callback_url>
    # - scope=<scopes>
    # - state=<random_string> (CSRF protection)
    # - code_challenge=<code_challenge> (PKCE)
    # - code_challenge_method=S256
    auth_url = oauth2_user_handler.get_authorization_url()
    
    print("\n" + "="*80)
    print("🔐 OAUTH 2.0 AUTHORIZATION REQUIRED")
    print("="*80)
    print("Following Twitter's OAuth 2.0 flow with PKCE:")
    print("1. Generated authorization URL with required parameters:")
    print("   ✓ response_type=code")
    print("   ✓ client_id (your app's client ID)")
    print("   ✓ redirect_uri (callback URL)")
    print("   ✓ scope (tweet.read tweet.write users.read offline.access)")
    print("   ✓ state (CSRF protection)")
    print("   ✓ code_challenge (PKCE security)")
    print("   ✓ code_challenge_method=S256")
    print("\n2. Please visit this URL to authorize the bot:")
    print(f"\n{auth_url}\n")
    print("3. After authorization, Twitter will redirect back to the callback")
    print("4. The bot will exchange the authorization code for an access token")
    print(f"\nCallback URL configured: {callback_url}")
    print("="*80 + "\n")
    
    logger.info(f"OAuth 2.0 authorization URL generated with PKCE: {auth_url}")
    logger.info(f"Callback URL: {callback_url}")

    # Step 2: Start local server to capture OAuth callback on port 5000
    global auth_response_url
    auth_response_url = None
    server = HTTPServer(('0.0.0.0', 5000), OAuthCallbackHandler)
    logger.info("Waiting for OAuth 2.0 callback on port 5000...")
    server.handle_request()
    server.server_close()

    # Step 3: Exchange authorization code for access token
    if auth_response_url:
        logger.info("Received OAuth callback, exchanging authorization code for access token...")
        # This handles the complete token exchange with PKCE verification
        access_token = oauth2_user_handler.fetch_token(auth_response_url)
        logger.info("✅ OAuth 2.0 access token obtained successfully")
        return access_token['access_token']
    else:
        logger.error("❌ Failed to receive OAuth callback")
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
        except Exception as e:
            logger.error(f"Unexpected error processing analysis request: {e}")

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
