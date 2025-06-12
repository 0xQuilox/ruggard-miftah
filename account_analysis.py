import tweepy
import logging
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AccountAnalyzer:
    def __init__(self, api):
        """
        Initialize account analyzer.
        :param api: Tweepy API instance
        """
        self.api = api
        self.sid = SentimentIntensityAnalyzer()
        self.suspicious_keywords = ['crypto', 'nft', 'giveaway', 'investment', 'earn money']

    def get_account_age(self, created_at):
        """
        Calculate account age in days.
        :param created_at: Account creation datetime
        :return: Age in days
        """
        try:
            age = (datetime.utcnow() - created_at).days
            return age
        except Exception as e:
            logger.error(f"Error calculating account age: {e}")
            return 0

    def analyze_bio(self, bio):
        """
        Analyze bio for length and suspicious keywords.
        :param bio: User bio string
        :return: Tuple (bio_length: int, is_suspicious: bool, message: str)
        """
        try:
            bio = bio or ""
            bio_length = len(bio)
            keywords_found = [kw for kw in self.suspicious_keywords if kw.lower() in bio.lower()]
            is_suspicious = len(keywords_found) > 0
            message = f"Bio length: {bio_length} chars"
            if is_suspicious:
                message += f"; Suspicious keywords: {', '.join(keywords_found)} ⚠️"
            else:
                message += " ✅"
            return bio_length, is_suspicious, message
        except Exception as e:
            logger.error(f"Error analyzing bio: {e}")
            return 0, False, "Bio analysis failed ⚠️"

    def analyze_engagement(self, user, tweets):
        """
        Analyze engagement patterns.
        :param user: Tweepy User object
        :param tweets: List of recent tweets
        :return: Dict with engagement metrics
        """
        try:
            total_likes = 0
            total_retweets = 0
            reply_count = 0
            tweet_count = len(tweets) or 1

            for tweet in tweets:
                total_likes += tweet.favorite_count
                total_retweets += tweet.retweet_count
                if tweet.in_reply_to_status_id:
                    reply_count += 1

            avg_likes = total_likes / tweet_count
            avg_retweets = total_retweets / tweet_count
            reply_ratio = reply_count / tweet_count

            return {
                'avg_likes': round(avg_likes, 2),
                'avg_retweets': round(avg_retweets, 2),
                'reply_ratio': round(reply_ratio, 2),
                'message': f"Avg likes: {avg_likes:.1f}, Avg retweets: {avg_retweets:.1f}, Reply ratio: {reply_ratio:.2f}"
            }
        except Exception as e:
            logger.error(f"Error analyzing engagement: {e}")
            return {
                'avg_likes': 0,
                'avg_retweets': 0,
                'reply_ratio': 0,
                'message': "Engagement analysis failed ⚠️"
            }

    def analyze_tweets(self, tweets):
        """
        Analyze sentiment and topics of recent tweets.
        :param tweets: List of Tweepy Status objects
        :return: Dict with sentiment and topic analysis
        """
        try:
            if not tweets:
                return {'sentiment': 'N/A', 'topics': [], 'message': "No tweets available ⚠️"}

            sentiments = []
            topics = set()
            for tweet in tweets:
                text = tweet.full_text if hasattr(tweet, 'full_text') else tweet.text
                # Sentiment analysis
                sentiment_scores = self.sid.polarity_scores(text)
                sentiments.append(sentiment_scores['compound'])
                # Topic extraction (simple keyword-based)
                words = re.findall(r'\w+', text.lower())
                for word in words:
                    if word in self.suspicious_keywords:
                        topics.add(word)

            avg_sentiment = sum(sentiments) / len(sentiments)
            sentiment_label = 'Positive' if avg_sentiment > 0.1 else 'Negative' if avg_sentiment < -0.1 else 'Neutral'
            topics_list = list(topics)
            message = f"Sentiment: {sentiment_label} ({avg_sentiment:.2f})"
            if topics_list:
                message += f"; Topics: {', '.join(topics_list)} ⚠️"
            else:
                message += " ✅"

            return {
                'sentiment': sentiment_label,
                'avg_sentiment': avg_sentiment,
                'topics': topics_list,
                'message': message
            }
        except Exception as e:
            logger.error(f"Error analyzing tweets: {e}")
            return {'sentiment': 'N/A', 'topics': [], 'message': "Tweet analysis failed ⚠️"}

    def analyze(self, user):
        """
        Perform full account analysis.
        :param user: Tweepy User object
        :return: Dict with all analysis results
        """
        try:
            # Fetch recent tweets
            tweets = self.api.user_timeline(
                screen_name=user.screen_name,
                count=20,
                tweet_mode='extended',
                exclude_replies=False
            )

            # Account age
            age = self.get_account_age(user.created_at)
            age_message = f"Age: {age} days {'✅' if age > 365 else '⚠️'}"

            # Follower/following ratio
            follower_ratio = user.followers_count / max(user.friends_count, 1)
            ratio_message = f"Follower ratio: {follower_ratio:.2f} {'✅' if follower_ratio > 0.5 else '⚠️'}"

            # Bio analysis
            bio_length, bio_suspicious, bio_message = self.analyze_bio(user.description)

            # Engagement analysis
            engagement = self.analyze_engagement(user, tweets)

            # Tweet analysis
            tweet_analysis = self.analyze_tweets(tweets)

            # Verification status
            verified_message = "Verified ✅" if user.verified else "Not verified ⚠️"

            # Compile summary
            summary = [
                verified_message,
                age_message,
                ratio_message,
                bio_message,
                engagement['message'],
                tweet_analysis['message']
            ]

            return {
                'verified': user.verified,
                'age': age,
                'follower_ratio': follower_ratio,
                'bio': {
                    'length': bio_length,
                    'suspicious': bio_suspicious,
                    'message': bio_message
                },
                'engagement': engagement,
                'tweets': tweet_analysis,
                'summary': '\n'.join(summary)
            }

        except tweepy.errors.TweepyException as e:
            logger.error(f"Tweepy error in analyze for {user.screen_name}: {e}")
            return {'summary': "Analysis failed due to API error ⚠️"}
        except Exception as e:
            logger.error(f"Unexpected error in analyze for {user.screen_name}: {e}")
            return {'summary': "Analysis failed ⚠️"}