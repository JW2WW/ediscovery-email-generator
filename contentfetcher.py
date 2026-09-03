import urllib.request
import xml.etree.ElementTree as ET
import json
import random
import re
import time

USER_AGENT = "Mozilla/5.0 (compatible; eDiscoveryTestMatrix/2.0)"

SENDERS = ["Sarah Chen", "Mike Torres", "Jennifer Walsh", "David Kim", "Lisa Park", "Tom Bradley"]
DEPARTMENTS = ["Finance", "Legal", "Operations", "Sales", "Engineering", "HR", "Procurement"]

SUBJECT_TEMPLATES = [
    "RE: {topic}",
    "FW: {topic}",
    "Please review: {topic}",
    "Action required: {topic}",
    "Updated: {topic}",
    "For your approval: {topic}",
    "Meeting follow-up: {topic}",
    "Quick question on {topic}",
    "{topic} - attached",
    "Draft for review: {topic}",
]

BODY_OPENERS = [
    "Hi,\n\nPlease see the attached file for your review.",
    "Hi team,\n\nAs discussed, I've attached the latest version below.",
    "Hello,\n\nCould you take a look at this when you get a chance?",
    "Hi,\n\nForwarding this along per our conversation earlier today.",
    "All,\n\nAttached is the document we discussed in yesterday's meeting.",
    "Hi,\n\nPlease find the updated file attached. Let me know if you have any questions.",
    "Good morning,\n\nI've pulled together the materials you requested.",
]

BODY_CLOSERS = [
    "\n\nThanks,\n{name}",
    "\n\nBest regards,\n{name}",
    "\n\nLet me know if you need anything else.\n\n{name}",
    "\n\nPlease respond by EOD if possible.\n\nThanks,\n{name}",
    "\n\nRegards,\n{name}\n{dept}",
]


def _clean_html(text):
    if not text:
        return ""
    return re.sub(r'<[^<]+?>', '', text).strip()


def _truncate(text, max_len=200):
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(' ', 1)[0] + "..."


def _wrap_as_business_email(raw_topic, raw_body):
    topic = _truncate(raw_topic.replace('\n', ' '), 80)
    topic = re.sub(r'^(Global Briefing|Technical Specification|Sysops Alert|Internal Record):\s*', '', topic)
    subject = random.choice(SUBJECT_TEMPLATES).format(topic=topic)
    sender = random.choice(SENDERS)
    dept = random.choice(DEPARTMENTS)
    body_content = _clean_html(raw_body)
    if len(body_content) > 500:
        body_content = body_content[:500].rsplit(' ', 1)[0] + "..."
    opener = random.choice(BODY_OPENERS)
    closer = random.choice(BODY_CLOSERS).format(name=sender, dept=dept)
    if random.random() > 0.6:
        body = f"{opener}\n\n{body_content}{closer}"
    else:
        body = f"{opener}{closer}"
    return subject, body


def fetch_un_news():
    url = "https://news.un.org/feed/subscribe/en/news/all/rss.xml"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=4) as r:
            root = ET.fromstring(r.read())
        items = root.findall('.//item')
        if items:
            chosen = random.choice(items)
            return chosen.find('title').text, chosen.find('description').text
    except Exception:
        return None, None


def fetch_arxiv_tech_data():
    url = "https://export.arxiv.org/api/query?search_query=all:infrastructure+OR+all:database+OR+all:cryptography&max_results=15"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=4) as r:
            root = ET.fromstring(r.read())
        namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', namespaces)
        if entries:
            chosen = random.choice(entries)
            title = chosen.find('atom:title', namespaces).text.strip().replace('\n', ' ')
            summary = chosen.find('atom:summary', namespaces).text.strip().replace('\n', ' ')
            return title, f"Abstract & Architecture Notes:\n{summary}"
    except Exception:
        return None, None


def fetch_github_dev_logs():
    url = "https://api.github.com/events"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=4) as r:
            events = json.loads(r.read().decode('utf-8'))
        push_events = [e for e in events if e['type'] == 'PushEvent']
        if push_events:
            event = random.choice(push_events)
            repo_name = event['repo']['name']
            commits = event['payload'].get('commits', [])
            if commits:
                commit_msg = commits[0]['message']
                body = f"Automated system update delivered to infrastructure cluster: {repo_name}\nCommit Message Details:\n{commit_msg}"
                return f"Change committed to {repo_name}", body
    except Exception:
        return None, None


def fetch_gutenberg_text():
    book_ids = [11, 2701, 1342, 84, 1661, 98]
    chosen_id = random.choice(book_ids)
    url = f"https://www.gutenberg.org/cache/epub/{chosen_id}/pg{chosen_id}.txt"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=4) as r:
            raw_text = r.read().decode('utf-8')
        lines = raw_text.split('\n')
        start_line = random.randint(1000, len(lines) - 100)
        body_snippet = "\n".join(lines[start_line:start_line + 20]).strip()
        subject = lines[start_line].strip()
        if len(subject) < 10:
            subject = f"Archive Update Segment #{chosen_id}"
        return subject, body_snippet
    except Exception:
        return None, None



def fetch_financial_news():
    # Simulate fetching financial news data.
    # In a real scenario, this would integrate with a financial news API.
    financial_headlines = [
        "Market Trends: Tech Sector Sees Q3 Growth",
        "Inflation Concerns Rise Amidst Global Supply Chain Issues",
        "Quarterly Earnings Report: Company X Exceeds Expectations",
        "Analysts Predict Moderate Growth for S&P 500 in Coming Months",
        "Cryptocurrency Volatility Continues: Investors Remain Cautious"
    ]
    financial_summaries = [
        "The tech sector has shown robust growth in the third quarter, driven by strong consumer demand for electronic goods and software services. This trend is expected to continue.",
        "Concerns about rising inflation are impacting global markets, with supply chain disruptions being a primary factor. Central banks are closely monitoring the situation.",
        "Company X announced its quarterly earnings today, reporting significant gains across all divisions. Revenue and profit figures surpassed analyst predictions.",
        "Financial analysts are forecasting a period of moderate, steady growth for the S&P 500. Investors are advised to remain diversified.",
        "The cryptocurrency market is still experiencing high volatility, leading many investors to adopt a more cautious approach. Regulatory discussions are ongoing."
    ]
    
    subject = random.choice(financial_headlines)
    body = random.choice(financial_summaries)
    return subject, body


def fetch_realistic_content():
    strategies = [fetch_un_news, fetch_arxiv_tech_data, fetch_github_dev_logs, fetch_gutenberg_text, fetch_financial_news]
    random.shuffle(strategies)
    for strategy in strategies:
        try:
            result = strategy()
            if result and isinstance(result, tuple) and len(result) == 2:
                raw_subject, raw_body = result
                if raw_subject and raw_body:
                    return _wrap_as_business_email(raw_subject, raw_body)
        except Exception:
            continue
    fallback_ts = int(time.time())
    return _wrap_as_business_email(
        f"Q3 budget review #{fallback_ts}",
        "Please review the attached spreadsheet and confirm the line items by Friday."
    )
