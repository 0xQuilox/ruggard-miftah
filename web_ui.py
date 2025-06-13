
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify
import logging

logger = logging.getLogger(__name__)

class BotStatusUI:
    def __init__(self, port=8080):
        self.app = Flask(__name__)
        self.port = port
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
