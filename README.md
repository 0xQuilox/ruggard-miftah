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
1. Clone the Repository
Clone the project to your local machine or Replit workspace:
bash

git clone https://github.com/your-username/ruggard.git
cd ruggard

2. Install Dependencies
Install the required Python libraries listed in requirements.txt:
bash

pip install -r requirements.txt

The dependencies are:
tweepy==4.14.0: For Twitter API interactions.

python-dotenv==1.0.0: For loading environment variables.

requests==2.31.0: For fetching the trusted list from GitHub.

vaderSentiment==3.3.2: For sentiment analysis of tweets.

textblob==0.18.0.post0: For additional text processing.

3. Configure API Keys
The bot requires Twitter API credentials and a bot handle. Configure these as environment variables:
Create a .env File (for local or non-Replit environments):
Copy .env.example to .env:
bash

cp .env.example .env

Edit .env with your Twitter API credentials and bot handle:
plaintext

CONSUMER_KEY=your_consumer_key
CONSUMER_SECRET=your_consumer_secret
ACCESS_TOKEN=your_access_token
ACCESS_TOKEN_SECRET=your_access_token_secret
BOT_HANDLE=YourBotHandle

Replace placeholders with actual values from the Twitter Developer Portal.

Replit Secrets (for Replit deployment):
In the Replit IDE, go to the “Secrets” tab (lock icon).

Add the following key-value pairs:
CONSUMER_KEY: Your Twitter API consumer key.

CONSUMER_SECRET: Your Twitter API consumer secret.

ACCESS_TOKEN: Your Twitter API access token.

ACCESS_TOKEN_SECRET: Your Twitter API access token secret.

BOT_HANDLE: Your bot’s Twitter handle (without @, e.g., RuggardBot).

4. Verify Trusted List Access
The bot fetches a trusted accounts list from https://github.com/devsyrem/turst-list/blob/main/list. Ensure the URL is accessible and the JSON format is correct (array of objects with handle fields). The list is cached in trusted_list.json for 24 hours to reduce API calls.
Running the Bot
Locally or on a Server
Make the Bash Script Executable:
bash

chmod +x run_bot.sh

Run the Bot:
bash

./run_bot.sh

This script creates a virtual environment, installs dependencies, loads environment variables, and starts bot.py in the background.

Logs are saved to bot.log.

Monitor Logs:
bash

tail -f bot.log

Stop the Bot:
Find the bot’s process ID (PID) from the script output.

Terminate it:
bash

kill <PID>

On Replit
Create a Repl:
Go to replit.com and create a new Python Repl.

Upload all project files (bot.py, account_analysis.py, trusted_accounts.py, requirements.txt, run_bot.sh).

Configure Secrets:
In the Replit IDE, go to the “Secrets” tab and add CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, and BOT_HANDLE.

Configure .replit:
Create or edit .replit in the project root:
plaintext

run = "bash run_bot.sh"

Test Locally:
Click “Run” in the Replit IDE or execute in the shell:
bash

./run_bot.sh

Test by tweeting “riddle me this” as a reply or mentioning @YourBotHandle.

Deploy on Reserved VM:
Go to the “Deployments” tab in Replit.

Select “Reserved VM” and deploy the project.

Monitor deployment logs and check bot.log for runtime errors.

Use a Shared CPU VM (starting at $0.20/day) for continuous operation.

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