# Ruggard: Twitter Trustworthiness Bot

Ruggard is a Twitter (X) bot that responds to replies containing the phrase "riddle me this" or mentions of the bot's handle under a tweet. It analyzes the trustworthiness of the original tweet's author and posts a concise summary of the analysis. The bot evaluates account age, follower/following ratio, bio content, engagement patterns, recent tweet sentiment, and checks if the author is followed by trusted accounts from a predefined list.

## Features

- **Trigger-Based Response**: Responds to "riddle me this" replies or bot mentions in tweet replies
- **Comprehensive Account Analysis**:
  - Account age (in days)
  - Follower-to-following ratio
  - Bio content analysis (length and suspicious keywords like "crypto", "NFT")
  - Engagement patterns (average likes, retweets, reply frequency)
  - Sentiment and topic analysis of recent tweets
- **Trusted Account Cross-Check**: Verifies if the author is followed by at least three accounts from a trusted list (sourced from GitHub)
- **Secure and Robust**:
  - Uses environment variables for API keys
  - Comprehensive logging with rotation
  - Handles Twitter API rate limits and errors gracefully
- **Modular Design**: Separates account analysis, trusted account checks, and bot logic for maintainability

## Project Structure

```
ruggard/
├── bot.py                # Main bot script for streaming and replying
├── account_analysis.py   # Module for analyzing account trustworthiness
├── trusted_accounts.py   # Module for trusted account cross-check
├── requirements.txt      # Python dependencies
├── run-bot.sh           # Bash script to run the bot (for local setup)
├── .env                 # Environment variables (create from .env.example)
├── .replit              # Replit configuration file
├── bot.log              # Log file (generated at runtime)
├── trusted_list.json    # Cached trusted accounts list (generated at runtime)
├── LICENSE              # MIT License
└── README.md            # This file
```

## Prerequisites

- **Twitter Developer Account**: Obtain API credentials from [developer.twitter.com](https://developer.twitter.com)
- **Replit Account**: Free account at [replit.com](https://replit.com) for cloud deployment
- **GitHub Access**: To fetch the trusted accounts list from the repository

## Twitter API Setup

### Step 1: Create Twitter Developer Account
1. Visit [developer.twitter.com](https://developer.twitter.com) and sign up
2. Create a new project and app
3. Set App Permissions to **Read and Write**
4. Enable **OAuth 2.0** in User Authentication Settings with:
   - Type of App: **Web App, Automated App, or Bot**
   - Website URL: `https://example.com` (temporary)
   - Callback URL: Will be updated after Replit deployment

### Step 2: Obtain API Credentials
You'll need these credentials:
- **Client ID** and **Client Secret** (OAuth 2.0)
- **Consumer Key**, **Consumer Secret**, **Access Token**, **Access Token Secret** (API v1.1)
- **Bearer Token** (API v2)

## Replit Deployment Setup

### Step 1: Create Replit Project
1. Sign up at [replit.com](https://replit.com)
2. Click **+ Create Repl**
3. Choose **Python** template
4. Name your Repl (e.g., "ruggard-bot")

### Step 2: Upload Project Files
1. Upload all project files to your Repl:
   - `bot.py`
   - `account_analysis.py`
   - `trusted_accounts.py`
   - `requirements.txt`
   - `.replit`
2. The dependencies will be automatically installed

### Step 3: Configure Environment Variables
1. Click the **Secrets** tab (lock icon) in your Replit workspace
2. Add these environment variables:

```
CONSUMER_KEY=your_consumer_key_here
CONSUMER_SECRET=your_consumer_secret_here
ACCESS_TOKEN=your_access_token_here
ACCESS_TOKEN_SECRET=your_access_token_secret_here
BOT_HANDLE=your_bot_handle_here
CLIENT_ID=your_oauth2_client_id_here
CLIENT_SECRET=your_oauth2_client_secret_here
```

**Important**: Do NOT use a `.env` file in Replit as it's less secure. Always use the Secrets tab.

### Step 4: Get Your Replit URL
1. Click the **Run** button once to start your Repl
2. Note your Replit URL (e.g., `https://ruggard-bot.username.repl.co`)
3. The OAuth callback URL will be: `https://ruggard-bot.username.repl.co/auth/twitter/callback`

### Step 5: Update Twitter Developer Portal
1. Go to your Twitter app in the Developer Portal
2. Navigate to **User Authentication Settings**
3. Update the **Callback URL** to: `https://your-repl-name.username.repl.co/auth/twitter/callback`
4. Save the changes

### Step 6: Deploy and Run
1. In Replit, click the **Run** button
2. The bot will start and show an authorization URL in the console
3. Open the authorization URL in a new tab
4. Log in with your bot's Twitter account
5. Click **Authorize app**
6. Return to Replit console to see "OAuth 2.0 access token obtained"
7. The bot is now running and monitoring for triggers

## Bot Usage

### How to Trigger the Bot
1. Find any public tweet you want to analyze
2. Reply to that tweet with either:
   - "riddle me this"
   - Mention your bot (e.g., "@RuggardBot")
3. The bot will analyze the original tweet's author and reply with a trustworthiness summary

### Example Interaction
User replies to @ExampleUser's tweet with: "riddle me this"

Bot responds:
```
@TriggerUser Trustworthiness of @ExampleUser:
✅ Verified
✅ Age: 730 days
✅ Follower ratio: 1.20
✅ Bio length: 50 chars
Avg likes: 10.5, Avg retweets: 5.2, Reply ratio: 0.30
✅ Sentiment: Neutral (0.00)
✅ Followed by 3 trusted accounts
```

## Architecture Overview

### Core Components

#### 1. bot.py (Main Bot Logic)
- **Purpose**: Main script that coordinates all bot functionality
- **Key Features**:
  - Twitter API v2 streaming for real-time tweet monitoring
  - OAuth 2.0 authentication handling
  - Rate limit management
  - Automatic crash recovery with 60-second restart delay
  - Comprehensive logging with file rotation (5MB limit, 5 backups)

#### 2. account_analysis.py (Account Analysis Engine)
- **Purpose**: Analyzes Twitter account trustworthiness metrics
- **Analysis Metrics**:
  - **Account Age**: Days since account creation
  - **Follower Ratio**: Followers/Following ratio (detects spam patterns)
  - **Bio Analysis**: Length and keyword detection (crypto, NFT, etc.)
  - **Engagement Patterns**: Average likes, retweets, reply frequency
  - **Content Analysis**: Sentiment analysis using VADER, topic extraction
- **Dependencies**: `tweepy`, `vaderSentiment`, `textblob`

#### 3. trusted_accounts.py (Trust Verification)
- **Purpose**: Cross-references accounts against a curated trusted list
- **Functionality**:
  - Fetches trusted accounts from GitHub repository
  - Caches list locally for 24 hours to reduce API calls
  - Uses Twitter's friendship API to verify connections
  - Marks users as trusted if followed by 2+ trusted accounts
- **Trust Threshold**: 3+ trusted followers = strong signal, 2+ = positive signal

### Data Flow
1. **Stream Monitoring**: Bot listens for trigger phrases in tweet replies
2. **Target Identification**: Extracts original tweet author for analysis
3. **Parallel Analysis**: Runs account analysis and trusted account check
4. **Response Generation**: Compiles analysis into 280-character summary
5. **Reply Posting**: Posts analysis as reply using Twitter API v1.1

## Configuration Options

### Environment Variables
```bash
# Required Twitter API Credentials
CONSUMER_KEY=your_consumer_key
CONSUMER_SECRET=your_consumer_secret
ACCESS_TOKEN=your_access_token
ACCESS_TOKEN_SECRET=your_access_token_secret
CLIENT_ID=your_oauth2_client_id
CLIENT_SECRET=your_oauth2_client_secret

# Bot Configuration
BOT_HANDLE=your_bot_handle  # Default: RuggardBot
```

### Customizable Parameters
In `trusted_accounts.py`:
- `cache_duration_hours`: How long to cache trusted list (default: 24)
- Trust threshold: Minimum trusted followers for positive signal (default: 2)

In `account_analysis.py`:
- Analysis timeframe: How many recent tweets to analyze (default: 20)
- Sentiment thresholds: Positive/negative sentiment boundaries

## Monitoring and Maintenance

### Log Files
- **Location**: `bot.log` in project root
- **Rotation**: 5MB max size, keeps 5 backup files
- **Log Levels**: INFO, WARNING, ERROR
- **Key Events**:
  - Authentication success/failure
  - Tweet processing
  - API rate limits
  - Crash recovery

### Performance Monitoring
```bash
# Check recent activity
tail -f bot.log

# Monitor rate limits
grep "rate limit" bot.log

# Check error frequency
grep "ERROR" bot.log | tail -20
```

## Troubleshooting

### Common Issues

#### 1. OAuth 2.0 Authentication Errors
**Error**: `(insecure_transport) OAuth 2 MUST utilize https`
**Solution**: 
- Ensure you're using the correct Replit HTTPS URL
- Update Twitter Developer Portal with the exact callback URL
- Verify the redirect URI in bot.py matches your Replit URL

#### 2. API Rate Limiting
**Error**: Rate limit exceeded messages in logs
**Solutions**:
- **Free Tier Limits**: 
  - 50 friendship lookups per 15 minutes
  - 1,500 tweets per month
- **Upgrade Options**: Consider Twitter API Basic tier ($100/month) for higher limits
- **Optimization**: Reduce trusted account list size in `trusted_accounts.py`

#### 3. Twitter API Credential Issues
**Error**: 401 Unauthorized or 403 Forbidden
**Solutions**:
- Verify all credentials in Replit Secrets
- Ensure your Twitter app has Read and Write permissions
- Check that your app is in a project with API v2 access
- Regenerate tokens if necessary

#### 4. Replit-Specific Issues
**Error**: Repl goes to sleep or stops responding
**Solutions**:
- **Free Tier**: Repls sleep after inactivity
- **Recommended**: Use Replit's Reserved VM deployment for 24/7 operation
- **Alternative**: Implement a keep-alive mechanism (ping service)

#### 5. Trusted List Fetch Errors
**Error**: Failed to fetch trusted list from GitHub
**Solutions**:
- Check internet connectivity
- Verify GitHub URL is accessible
- Use cached version if available
- Implement fallback trusted accounts list

### Debug Commands

```bash
# Check if bot is responding
grep "Processing trigger" bot.log | tail -5

# Monitor authentication
grep "OAuth" bot.log | tail -3

# Check API errors
grep "TweepyException" bot.log | tail -10

# View recent crashes
grep "Bot crashed" bot.log | tail -5
```

## API Rate Limits and Costs

### Twitter API Free Tier
- **Tweet Cap**: 1,500 tweets per month
- **Friendship Lookups**: 50 per 15-minute window
- **Streaming**: 25 concurrent stream connections
- **Suitable For**: Testing and low-volume usage

### Twitter API Basic Tier ($100/month)
- **Tweet Cap**: 50,000 tweets per month
- **Friendship Lookups**: 300 per 15-minute window
- **Streaming**: Unlimited concurrent connections
- **Suitable For**: Production deployment

## Security Best Practices

### Credential Management
- ✅ **Use Replit Secrets**: Never hardcode API keys
- ✅ **Regular Rotation**: Rotate API keys periodically
- ✅ **Principle of Least Privilege**: Only request necessary Twitter permissions

### Code Security
- ✅ **Input Validation**: All user inputs are sanitized
- ✅ **Error Handling**: Comprehensive exception handling prevents crashes
- ✅ **Logging**: No sensitive data logged

### Network Security
- ✅ **HTTPS Only**: All API calls use HTTPS
- ✅ **Certificate Validation**: TLS certificates are properly validated
- ✅ **Rate Limiting**: Built-in protection against abuse

## Deployment for Production

### Replit Reserved VM Setup
1. **Upgrade Account**: Get Replit subscription for Reserved VM access
2. **Configure Deployment**: 
   - Go to Deployments tab in your Repl
   - Choose "Reserved VM" deployment type
   - Set run command: `python bot.py`
3. **Monitor Performance**: Use Replit's built-in monitoring tools
4. **Set Up Alerts**: Configure notifications for downtime

### Scaling Considerations
- **Multiple Bots**: Deploy separate instances for different trigger phrases
- **Geographic Distribution**: Use multiple Replit regions for global coverage
- **Load Balancing**: Implement webhook-based architecture for high volume

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup
1. Fork the repository
2. Create a new Repl from your fork
3. Set up environment variables in Secrets
4. Make your changes
5. Test thoroughly with a test Twitter account

### Contribution Guidelines
- **Code Style**: Follow PEP 8 guidelines
- **Testing**: Include test cases for new features
- **Documentation**: Update README.md for new features
- **Commit Messages**: Use clear, descriptive commit messages

### Types of Contributions
- 🐛 **Bug Fixes**: Fix issues with existing functionality
- ✨ **New Features**: Add new analysis metrics or bot capabilities
- 📚 **Documentation**: Improve setup guides and troubleshooting
- 🔧 **Performance**: Optimize API usage and response times

## FAQ

### Q: How much does it cost to run the bot?
**A**: The free Twitter API tier allows 1,500 tweets/month, suitable for testing. For production, expect $100/month for Twitter API Basic tier plus Replit hosting costs.

### Q: Can I run multiple bots with different handles?
**A**: Yes, create separate Replit projects with different Twitter apps and bot handles.

### Q: How accurate is the trustworthiness analysis?
**A**: The analysis combines multiple metrics for a comprehensive view, but should be used as guidance rather than definitive truth.

### Q: Can I customize the analysis criteria?
**A**: Yes, modify `account_analysis.py` to adjust weights, thresholds, and add new metrics.

### Q: What happens if the trusted accounts list is unavailable?
**A**: The bot uses cached data and falls back to account-only analysis if the GitHub list is inaccessible.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: This README covers most use cases
- **Community**: Join discussions in GitHub Discussions

## Changelog

### Version 1.0.0
- Initial release with core functionality
- Account analysis engine
- Trusted account verification
- Replit deployment support
- Comprehensive logging and error handling

---

**Note**: This bot is designed for educational and research purposes. Always respect Twitter's Terms of Service and API usage guidelines.