from apify_client import ApifyClient
import random

# ── Keyword → Facebook Page URL mapping ──────────────────────
PAGES = {
    'tesla': 'https://www.facebook.com/TeslaMotorsCo',
    'apple': 'https://www.facebook.com/apple',
    'google': 'https://www.facebook.com/Google',
    'microsoft': 'https://www.facebook.com/Microsoft',
    'amazon': 'https://www.facebook.com/Amazon',
    'netflix': 'https://www.facebook.com/netflix',
    'nasa': 'https://www.facebook.com/NASA',
    'nike': 'https://www.facebook.com/nike',
    'samsung': 'https://www.facebook.com/SamsungUS',
    'bitcoin': 'https://www.facebook.com/bitcoinofficial',
    'iphone': 'https://www.facebook.com/apple',
    'ai': 'https://www.facebook.com/MetaAI',
    'meta': 'https://www.facebook.com/Meta',
    'bbc': 'https://www.facebook.com/BBCNews',
    'cnn': 'https://www.facebook.com/cnn',
    'climate': 'https://www.facebook.com/climaterealityproject',
    'health': 'https://www.facebook.com/WHO',
    'who': 'https://www.facebook.com/WHO',
    'spacex': 'https://www.facebook.com/SpaceX',
    'openai': 'https://www.facebook.com/MetaAI',
    'twitter': 'https://www.facebook.com/xplatformofficial',
    'crypto': 'https://www.facebook.com/cnn',
    'nba': 'https://www.facebook.com/NBA',
    'fifa': 'https://www.facebook.com/fifaworldcup',
    'india': 'https://www.facebook.com/BBCNews',
    'sport': 'https://www.facebook.com/NBA',
    'food': 'https://www.facebook.com/BBCFood',
    'travel': 'https://www.facebook.com/NatGeo',
    'science': 'https://www.facebook.com/NASA',
    'tech': 'https://www.facebook.com/TechCrunch',
}

DEFAULT_PAGE = 'https://www.facebook.com/BBCNews'


def _get_page_url(keyword):
    """Map a keyword to the best matching Facebook page URL."""
    kw = keyword.lower().strip()
    # Exact match first
    if kw in PAGES:
        return PAGES[kw]
    # Partial match
    for k, url in PAGES.items():
        if k in kw or kw in k:
            return url
    return DEFAULT_PAGE


def fetch_facebook_posts(keyword, max_posts=50, apify_token=''):
    """
    Fetch Facebook posts with 40% real Apify data + 60% demo data.
    Always returns exactly max_posts total posts.
    Falls back to 100% demo if Apify fails or no token provided.
    """

    real_posts = []
    real_target = int(max_posts * 0.4)   # 40% = real posts

    # ── Try Apify first ───────────────────────────────────────
    if apify_token and apify_token not in ('', 'YOUR_APIFY_TOKEN_HERE'):
        page_url = _get_page_url(keyword)

        print(f"🔄 Apify scraping {real_target} posts from: {page_url}")

        try:
            client = ApifyClient(apify_token)
            run_input = {
                "startUrls": [{"url": page_url}],
                "resultsLimit": real_target,
                "scrapePosts": True,
                "scrapeAbout": False,
                "scrapeReviews": False,
                "proxyConfiguration": {"useApifyProxy": True},
            }

            run = client.actor("apify/facebook-posts-scraper").call(
                run_input=run_input
            )
            real_posts = list(
                client.dataset(run["defaultDatasetId"]).iterate_items()
            )

            if real_posts:
                print(f"✅ Got {len(real_posts)} REAL posts from Apify")
            else:
                print("⚠️  Apify returned 0 posts — filling with demo data")

        except Exception as e:
            print(f"❌ Apify error: {e} — filling with demo data")
            real_posts = []
    else:
        print("⚠️  No Apify token provided — using 100% demo data")

    # ── Normalize real posts to standard format ───────────────
    normalized_real = []
    for item in real_posts:
        normalized_real.append({
            'id': str(item.get('id',
                               f'real_{random.randint(1000, 9999)}')),
            'text': item.get('text') or
            item.get('message',    ''),
            'message': item.get('text') or
            item.get('message',    ''),
            'authorName': item.get('authorName') or
            item.get('pageName',   'Facebook User'),
            'pageName': item.get('pageName') or
            item.get('authorName', 'Facebook Page'),
            'likesCount': (item.get('likesCount') or
                           item.get('likes',    0)),
            'sharesCount': (item.get('sharesCount') or
                            item.get('shares',   0)),
            'commentsCount': (item.get('commentsCount') or
                              item.get('comments', 0)),
            'url': item.get('url', ''),
            'time': (item.get('time') or
                     item.get('timestamp', '')),
            'source': '🔴 Live',
        })

    # ── Generate demo posts to fill the rest (60%) ───────────
    demo_needed = max(0, max_posts - len(normalized_real))
    demo_posts = _demo(keyword, demo_needed)

    # ── Merge real + demo, then shuffle ──────────────────────
    merged = normalized_real + demo_posts
    random.shuffle(merged)

    real_count = len(normalized_real)
    demo_count = len(demo_posts)
    total = len(merged)

    if total > 0:
        print(
            f"📦 Final dataset: "
            f"{real_count} real ({int(real_count/total*100)}%) + "
            f"{demo_count} demo ({int(demo_count/total*100)}%) "
            f"= {total} total posts for '{keyword}'"
        )

    return merged


# ── Demo Data Generator ───────────────────────────────────────

def _demo(keyword, count=50):
    """Generate realistic demo posts for any keyword."""

    if count <= 0:
        return []

    authors = [
        'TechEnthusiast99', 'MarketWatcher',    'GlobalNewsToday',
        'SocialBuzz',       'TrendAlert',        'DataDriven_Ana',
        'CryptoFan2025',    'GreenEarthNow',     'SportsFanatic',
        'FoodieWorld',      'TravelBlogger',     'StartupMindset',
        'AIResearcher',     'HealthFirst',        'MusicLover22',
        'BusinessInsider',  'TechCrunchFan',     'InvestorMindset',
        'ScienceDaily',     'NewsBreaker',        'PolicyWatch',
        'DataNerd',         'EcoWarrior',         'DigitalNomad',
        'CommunityVoice',   'TrendWatcher',      'GlobalCitizen',
        'FutureThinker',    'AnalyticsGuru',     'SocialMediaPro',
    ]

    kw = keyword
    kwt = keyword.replace(' ', '')

    templates = [
        # ── Positive ─────────────────────────────────────────
        f"Just read about {kw} — absolutely fascinating! "
        f"#trending #{kwt} #viral",
        f"Breaking: New {kw} developments could change everything 🔥 "
        f"@TechEnthusiast99 #{kwt}",
        f"{kw} is dominating the news today. "
        f"5 things you NEED to know! #breaking #news",
        f"My honest thoughts on {kw}: complete game changer 💪 "
        f"#opinion #{kwt}",
        f"{kw} performance is through the roof! 📈 "
        f"#winning #{kwt} #growth",
        f"Community update: {kw} campaign hit 10k supporters! "
        f"Thank you all ❤️ #community",
        f"We tested {kw} for 30 days — completely honest results 📊 "
        f"#review #honest",
        f"New scientific study confirms {kw} has major real-world impact. "
        f"Details inside 🔬",
        f"Record-breaking numbers for {kw} this quarter. "
        f"Wall Street takes notice 💰 #stocks",
        f"How {kw} transformed my business in just 3 months. "
        f"Full story! #success #{kwt}",
        f"Just attended a {kw} webinar. "
        f"Mind completely blown 🤯 #learning #growth",
        f"Why {kw} matters for the future. "
        f"Long thread but worth reading 📖 @AIResearcher",
        f"{kw} supporters rally worldwide. "
        f"Historic moment! #history #global #{kwt}",
        f"New report: {kw} could save millions of lives. "
        f"#hope #future #impact",
        f"How I grew my following 300% posting about {kw}. "
        f"Full strategy here 🚀 #{kwt}",
        f"Excited to share full analysis of {kw} trends. "
        f"Data is very surprising! #data #analytics",

        # ── Negative ─────────────────────────────────────────
        f"I'm deeply disappointed with {kw}. "
        f"Here's why I changed my mind 😔 #opinion",
        f"URGENT: {kw} update everyone needs to see. "
        f"This affects us all! #urgent #important",
        f"The hidden side of {kw} that mainstream media ignores. "
        f"#exposing #truth",
        f"Warning: Misinformation about {kw} is spreading fast. "
        f"Real facts below ✅ #fakenews",
        f"Government announces major new {kw} policy. "
        f"This changes everything #policy #law",
        f"Why {kw} is the worst thing to happen this year. "
        f"Unpopular opinion 🤔 #{kwt}",
        f"Major problems with {kw} nobody is discussing. "
        f"This needs attention! #serious",
        f"Controversy surrounds {kw} as experts disagree. "
        f"Full debate 🔥 #{kwt} #debate",
        f"Completely failed by {kw} today. "
        f"Here's my experience 😤 #disappointed",

        # ── Neutral ───────────────────────────────────────────
        f"Live {kw} updates — follow for breaking developments! "
        f"🔴 #{kwt} #live",
        f"Has anyone noticed how {kw} is changing rapidly? "
        f"Thoughts? 💭 #discussion",
        f"Just shared my full research paper on {kw}. "
        f"47 pages of deep analysis 📄 #research",
        f"Major corporation invests $2B in {kw}. "
        f"What this means for consumers 💰 #business",
        f"Opinion: {kw} is either the best or worst thing this year. "
        f"Discuss! 🤔 #{kwt}",
        f"New {kw} data just released. "
        f"Processing the implications… #analysis #data",
        f"Asked 100 people about {kw}. "
        f"Their responses were surprising! 👇 #survey",
        f"Comparing {kw} with alternatives — "
        f"full breakdown inside 📋 #comparison",
        f"Interview with top expert on {kw}. "
        f"Key takeaways and what to watch 🎙️",
        f"Thread: Everything you need to know about {kw} "
        f"in 2025 🧵 #{kwt}",
    ]

    posts = []
    for i in range(min(count, 500)):
        tmpl = templates[i % len(templates)]
        author = authors[i % len(authors)]

        # Realistic engagement: most posts get low likes, few go viral
        likes = random.choices(
            population=[
                random.randint(0,    50),
                random.randint(50,   500),
                random.randint(500,  5000),
                random.randint(5000, 50000),
            ],
            weights=[40, 35, 20, 5]
        )[0]

        shares = int(likes * random.uniform(0.05, 0.35))
        comments = int(likes * random.uniform(0.03, 0.20))

        # Spread timestamps realistically across Jan–Apr 2025
        month = random.randint(1, 4)
        day = random.randint(1, 28)
        # Peak hours: morning (8-9), lunch (12-13), evening (19-21)
        hour = random.choices(
            population=list(range(24)),
            weights=[1, 1, 1, 1, 1, 2, 3, 5, 7, 8, 8,
                     9, 8, 8, 9, 9, 8, 7, 8, 9, 8, 6, 4, 2]
        )[0]

        posts.append({
            'id': f'demo_{i + 1}_{random.randint(100, 999)}',
            'text': tmpl,
            'message': tmpl,
            'authorName': author,
            'pageName': author,
            'likesCount': likes,
            'sharesCount': shares,
            'commentsCount': comments,
            'url': f'https://facebook.com/post/demo_{i + 1}',
            'time': f'2025-{month:02d}-{day:02d}T{hour:02d}:00:00',
            'source': '🔵 Demo',
        })

    print(f"📝 Generated {len(posts)} demo posts for '{keyword}'")
    return posts
