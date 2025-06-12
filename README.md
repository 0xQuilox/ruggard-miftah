# Ruggard: Twitter Trustworthiness Bot

Ruggard is a Twitter (X) bot that responds to replies containing the phrase "riddle me this" or mentions of the bot’s handle under a tweet. It analyzes the trustworthiness of the original tweet’s author and posts a concise summary of the analysis. The bot evaluates account age, follower/following ratio, bio content, engagement patterns, recent tweet sentiment, and checks if the author is followed by trusted accounts from a predefined list.

## Features

Trigger-Based Response: Responds to "riddle me this" replies or bot mentions in tweet replies.

Account Analysis:

Account age (in days).

Follower-to-following ratio.

Bio content (length and suspicious keywords like "crypto", "NFT").

Engagement patterns (average likes, retweets, reply frequency).

Sentiment and topic analysis of recent tweets.

Trusted Account Cross-Check: Verifies if the author is followed by at least three accounts from a trusted list (sourced from GitHub). A positive signal is given if followed by two or more trusted accounts.

Secure and Robust:

Uses environment variables for API keys.

Comprehensive logging with rotation.

Handles Twitter API rate limits and errors gracefully.

Modular Design: Separates account analysis, trusted account checks, and bot logic for maintainability.

## Project Structure

ruggard/
├── bot.py                # Main bot script for streaming and replying
├── account_analysis.py   # Module for analyzing account trustworthiness
├── trusted_accounts.py   # Module for trusted account cross-check
├── requirements.txt      # Python dependencies
├── run_bot.sh           # Bash script to run the bot
├── .env.example         # Template for environment variables
├── bot.log              # Log file (generated at runtime)
└── trusted_list.json    # Cached trusted accounts list (generated at runtime)

## Prerequisites
Python 3.7+: Required to run the bot.

Twitter Developer Account: Obtain API credentials from developer.twitter.com.

Replit Account (optional): For deployment on Replit’s Virtual Machine.

GitHub Access: To fetch the trusted accounts list from https://github.com/devsyrem/turst-list.

## Setup and Installation
The Ruggard Twitter bot monitors tweets and replies with trustworthiness analyses of mentioned accounts. This guide provides two setup options: local setup using a Python virtual environment with Serveo for HTTPS tunneling, and cloud setup using Replit for a permanent HTTPS callback URL. Both setups use Twitter API v2 for streaming and v1.1 for posting replies.

Prerequisites
- Twitter Developer Account:
  - Create an app in the Twitter Developer Portal (https://developer.twitter.com).
  - Set App Permissions to Read and Write.
  - Enable OAuth 2.0 in User Authentication Settings with:
    - Type of App: Web App, Automated App, or Bot.
    - Website URL: https://example.com.
  - Obtain:
    - Client ID and Client Secret (OAuth 2.0).
    - Consumer Key, Consumer Secret, Access Token, Access Token Secret (API v1.1).

- Local Setup:
  - Python 3.12 (recommended; 3.13+ requires imghdr patch).
  - Git (optional, for cloning).
  - Windows, macOS, or Linux with an SSH client (Windows 10/11 includes OpenSSH).
  - VS Code or another code editor (optional).

- Replit Setup:
  - Free account at https://replit.com.
  - Internet browser.

### Local Setup

This setup runs the bot on your machine using a Python virtual environment and Serveo for HTTPS tunneling to handle Twitter OAuth 2.0 callbacks.

Step 1: Clone or Download the Repository
1. Clone the repository (requires Git): git clone <repository-url>
   cd ruggard-miftah

2. Or download and extract the ZIP file to a folder (e.g., C:\Users\YourUsername\ruggard-miftah).

Step 2: Set Up Python Virtual Environment
1. Navigate to the project folder: cd C:\Users\YourUsername\ruggard-miftah

2. Create a virtual environment: python -m venv venv

3. Activate the virtual environment:
- Windows (PowerShell or Command Prompt):
  ```
  .\venv\Scripts\Activate.ps1
  ```
- macOS/Linux:
  ```
  source venv/bin/activate
  ```

Step 3: Install Dependencies
1. Ensure requirements.txt contains:
   tweepy==4.14.0
   python-dotenv==1.0.0
   requests==2.31.0
   vaderSentiment==3.3.2
   textblob==0.18.0.post0


3. Install dependencies: pip install -r requirements.txt

Step 4: Configure Environment Variables
1. Create a .env file in the project root:
   CONSUMER_KEY=your_consumer_key
   CONSUMER_SECRET=your_consumer_secret
   ACCESS_TOKEN=your_access_token
   ACCESS_TOKEN_SECRET=your_access_token_secret
   BOT_HANDLE=RuggardBot
   CLIENT_ID=your_oauth2_client_id
   CLIENT_SECRET=your_oauth2_client_secret


2. Replace placeholders with your Twitter API credentials.

Step 5: Set Up Serveo for HTTPS Tunneling
Serveo provides an HTTPS callback URL for Twitter OAuth 2.0 without local installations.

1. Verify SSH client:
- On Windows:
  ```
  ssh -V
  ```
- If missing, enable OpenSSH: Settings > Apps > Optional Features > Add a feature > OpenSSH Client.
- On macOS/Linux, SSH is typically pre-installed.

2. Start Serveo tunnel: ssh -R 80:localhost:3000 serveo.net
- Output shows an HTTPS URL, e.g., https://randomsubdomain.serveo.net.
- Copy the URL. The callback URL is https://randomsubdomain.serveo.net/auth/twitter/callback.
- Keep the terminal open.

3. Update Twitter Developer Portal:
- Go to Projects & Apps > YourApp > Edit > User Authentication Settings.
- Add the callback URL (e.g., https://randomsubdomain.serveo.net/auth/twitter/callback).
- Save.

Step 6: Run the Bot
1. Open a new terminal in the project folder (keep Serveo running).
2. Activate the virtual environment (if not active):  .\venv\Scripts\Activate.ps1

3. Run the bot:  python bot.py
4. Enter the Serveo HTTPS URL (e.g., https://randomsubdomain.serveo.net) when prompted.
5. A browser opens for Twitter authorization:
- Log in with the bot's Twitter account (e.g., @RuggardBot).
- Click Authorize App.
- The browser shows: "Authentication successful. You can close this window."
6. Check bot.log for confirmation: cat bot.log  # Windows: Get-Content bot.log -Tail 1
- Expect:
  ```
  2025-06-12 23:00:00,123 - INFO - Twitter API v1.1 initialized successfully
  2025-06-12 23:00:01,456 - INFO - OAuth 2.0 access token obtained
  2025-06-12 23:00:02,789 - INFO - Stream started successfully
  ```

Step 7: Test the Bot
1. Using a secondary Twitter account, reply to a public tweet on https://x.com with:
- "riddle me this"
- @RuggardBot
- Example:
  - @TestUser tweets: "Test tweet!"
  - Reply: "riddle me this"
2. The bot should reply, e.g.:
   @YourTestAccount

 Trustworthiness of @TestUser

:
   Verified 
   Age: 730 days 
   Follower ratio: 1.20 
   Bio length: 50 chars 
   Avg likes: 10.5, Avg retweets: 5.2, Reply ratio: 0.30
   Sentiment: Neutral (0.00) 
   Followed by 3 trusted accounts 


3. Check bot.log for:   2025-06-12 23:01:00,789 - INFO - Processing trigger from @YourTestAccount


### Replit Setup

This setup runs the bot on Replit, providing a permanent HTTPS callback URL without local tunneling.

Step 1: Create a Replit Account
1. Sign up at https://replit.com.

Step 2: Create a Python Repl
1. Click + New Repl > Python.
2. Upload project files (bot.py, requirements.txt, trusted_accounts.py, account_analysis.py) via drag-and-drop or import from Git.

Step 3: Install Dependencies
1. Open requirements.txt in Replit and ensure it includes:



   tweepy==4.14.0
   python-dotenv==1.0.0
   requests==2.31.0
   vaderSentiment==3.3.2
   textblob==0.18.0.post0





Example Bot Interaction
A user replies to a tweet by @ExampleUser with “riddle me this” or mentions @RuggardBot.

The bot analyzes @ExampleUser and responds with a summary like:

@TriggerUser Trustworthiness of @ExampleUser:
Verified ✅
Age: 730 days ✅
Follower ratio: 1.20 ✅
Bio length: 50 chars ✅
Avg rebates: 10.5, Avg retweets: 5.2, Reply ratio: 0.30
Sentiment: Neutral (0.00) ✅
Followed by 3 trusted accounts ✅

## Architecture and Key Modules
Ruggard is designed with a modular architecture for maintainability and scalability. Below are the key components:
1. bot.py
Purpose: Main script that initializes the Twitter API, monitors tweets, and coordinates responses.

Functionality:
Uses Tweepy’s streaming API to listen for “riddle me this” or bot mentions in replies.

Fetches the original tweet’s author and triggers analysis via AccountAnalyzer and TrustedAccounts.

Posts a concise reply (within 280 characters) summarizing trustworthiness.

Features:
Handles Twitter API rate limits with wait_on_rate_limit=True.

Logs all activity to bot.log with rotation (5MB limit, 5 backups).

Restarts automatically after crashes with a 60-second delay.

2. account_analysis.py
Purpose: Analyzes the trustworthiness of a Twitter account.

Functionality:
Account Age: Calculates days since account creation.

Follower/Following Ratio: Computes ratio to detect spam-like accounts.

Bio Content: Checks bio length and suspicious keywords (e.g., “crypto”, “NFT”).

Engagement Patterns: Analyzes average likes, retweets, and reply frequency for recent tweets.

Tweet Content: Performs sentiment analysis (using VADER) and topic extraction (using TextBlob and keyword matching).

Dependencies: tweepy, vaderSentiment, textblob.

3. trusted_accounts.py
Purpose: Checks if a user is followed by trusted accounts from a predefined list.

Functionality:
Fetches the trusted list from GitHub and caches it in trusted_list.json for 24 hours.

Uses Tweepy’s get_friendship to check if trusted accounts follow the target user.

Marks the user as trusted if followed by at least two trusted accounts (three or more is a strong signal).

Dependencies: tweepy, requests.

4. run_bot.sh
Purpose: Bash script to set up and run the bot.

## Functionality:
Creates a virtual environment and installs dependencies.

Loads environment variables from .env or exported variables.

Runs bot.py in the background and logs to bot.log.

Provides commands to monitor or stop the bot.

## Security Considerations
API Keys: Stored in Replit Secrets or .env (excluded from version control via .gitignore).

Logging: Sensitive data (e.g., API keys) is not logged. Logs are rotated to prevent excessive disk usage.

Rate Limits: Tweepy handles Twitter API rate limits automatically.

Input Validation: Sanitizes Twitter handles and text to prevent injection attacks.

Network Security: Uses HTTPS for GitHub requests and Twitter API calls.

## Troubleshooting
Bot Not Responding:
Check bot.log for errors (e.g., authentication failures, rate limits).

Verify Twitter API credentials in Replit Secrets or .env.

## Rate Limit Issues:
Twitter’s free API tier has strict limits (e.g., 50 friendship lookups per 15 minutes). Consider upgrading to the Basic tier ($100/month).

Trusted List Errors:
Ensure the GitHub URL is accessible and JSON format is correct.

Increase cache duration in trusted_accounts.py if GitHub rate limits are hit.

Replit Sleeping:
Free Repls sleep after inactivity. Use a Reserved VM Deployment for continuous operation.

## Dependency Issues:
Run pip install -r requirements.txt in the Replit shell if installation fails.

Contributing
Contributions are welcome! To contribute:
Fork the repository.

Create a feature branch (git checkout -b feature/your-feature).

Commit changes (git commit -m "Add your feature").

Push to the branch (git push origin feature/your-feature).

Open a pull request.

Please ensure code follows PEP 8 style guidelines and includes tests where applicable.
License
This project is licensed under the MIT License. See LICENSE for details.

## Contact
For issues or questions, open an issue on GitHub or contact the maintainer at [you (miftahudeentajudeen@gmail.com)].
Notes
Repository Reference: The README.md assumes the project will be hosted on GitHub (0xQuilox).

Replit Deployment: The instructions prioritizeelne Replit-specific steps, emphasizing the Reserved VM for continuous operation.

Customization: Adjust the contact email or add a license file if needed.

Trusted List: The GitHub URL is included as specified; ensure it remains valid or update if necessary.

Testing: Encourage users to test locally before deploying to catch configuration issues early.
