
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import logging

logger = logging.getLogger(__name__)

class BotStatusUI:
    def __init__(self, port=8080):
        self.app = Flask(__name__)
        self.port = port
        self.oauth_handler = None
        self.bot_status = {
            'running': False,
            'last_activity': None,
            'start_time': None,
            'oauth_status': 'Not Started',
            'stream_status': 'Disconnected',
            'tweets_processed': 0,
            'errors_count': 0,
            'last_error': None
        }
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def get_status():
            return jsonify(self.bot_status)
        
        @self.app.route('/api/logs')
        def get_logs():
            try:
                with open('bot.log', 'r') as f:
                    logs = f.readlines()[-50:]  # Last 50 lines
                return jsonify({'logs': logs})
            except Exception as e:
                return jsonify({'logs': [f'Error reading logs: {str(e)}']})
        
        @self.app.route('/auth/twitter/callback')
        @self.app.route('/')
        def twitter_callback():
            """Handle Twitter OAuth 2.0 callback at both /auth/twitter/callback and / paths"""
            try:
                # Get authorization code from callback
                code = request.args.get('code')
                state = request.args.get('state')
                error = request.args.get('error')
                
                # If no OAuth parameters, show dashboard instead
                if not code and not error and not state:
                    return render_template('dashboard.html')
                
                if error:
                    logger.error(f"OAuth callback error: {error}")
                    return f"<h2>OAuth Error</h2><p>{error}</p>"
                
                if not code:
                    logger.error("No authorization code received")
                    return "<h2>OAuth Error</h2><p>No authorization code received</p>"
                
                logger.info(f"OAuth callback received with code: {code[:10]}...")
                
                # Exchange code for access token
                import tweepy
                import os
                
                CLIENT_ID = os.getenv('CLIENT_ID')
                CLIENT_SECRET = os.getenv('CLIENT_SECRET')
                
                # Import oauth_tokens from bot module
                import sys
                if 'bot' in sys.modules:
                    from bot import oauth_tokens
                else:
                    # Fallback if bot module not loaded yet
                    oauth_tokens = {}
                
                # Create OAuth2 handler with the same configuration as in bot.py
                oauth2_user_handler = tweepy.OAuth2UserHandler(
                    client_id=CLIENT_ID,
                    redirect_uri=request.url_root.replace('http://', 'https://').rstrip('/') + '/',
                    scope=["tweet.read", "tweet.write", "users.read", "follows.read"],
                    client_secret=CLIENT_SECRET
                )
                
                # Fetch the token using the full callback URL
                full_callback_url = request.url.replace('http://', 'https://')
                access_token = oauth2_user_handler.fetch_token(
                    authorization_response=full_callback_url
                )
                
                oauth_tokens['access_token'] = access_token
                logger.info("OAuth 2.0 authentication successful!")
                logger.info(f"Access token obtained: {access_token.get('access_token', 'N/A')[:10]}...")
                
                return """
                <html>
                    <head><title>OAuth Success</title></head>
                    <body style='font-family: Arial, sans-serif; text-align: center; padding: 50px;'>
                        <h2 style='color: #1DA1F2;'>✅ Authentication Successful!</h2>
                        <p>The bot has been successfully authenticated with Twitter.</p>
                        <p>You can now close this window and return to your bot.</p>
                        <script>
                            setTimeout(function() {
                                window.close();
                            }, 3000);
                        </script>
                    </body>
                </html>
                """
                
            except Exception as e:
                logger.error(f"OAuth callback processing error: {e}")
                return f"<h2>OAuth Error</h2><p>Failed to process callback: {str(e)}</p>"
    
    def update_status(self, **kwargs):
        """Update bot status"""
        for key, value in kwargs.items():
            if key in self.bot_status:
                self.bot_status[key] = value
        self.bot_status['last_activity'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def start_server(self):
        """Start the web UI server in a separate thread"""
        def run_server():
            try:
                self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
            except Exception as e:
                logger.error(f"Web UI server error: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        logger.info(f"Web UI started on port {self.port}")

# Global instance for bot.py to use
ui_instance = BotStatusUI()
