import feedparser
import random

def fetch_latest_news():
    feeds = [
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "http://feeds.bbci.co.uk/news/rss.xml"
    ]
    selected_feed = random.choice(feeds)
    parsed = feedparser.parse(selected_feed)
    
    if parsed.entries:
        item = random.choice(parsed.entries)
        return item.title, item.summary
    return "Default Subject", "Default body text if feed fails."
