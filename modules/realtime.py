from datetime import datetime, timedelta
from collections import defaultdict
from modules.sentiment import analyze_sentiment


def get_realtime_stats(posts, hours=24):
    """
    Simulate real-time monitoring stats from collected posts.
    Groups activity into hourly buckets and checks for sentiment spikes.
    """

    if not posts:
        return {}

    now = datetime.utcnow()
    cutoff = now - timedelta(hours=hours)

    # Recent posts (last N hours or all if less data)
    recent = [p for p in posts if p.created_at and p.created_at >= cutoff]
    if not recent:
        recent = posts[-20:]   # fallback: last 20

    # Sentiment breakdown of recent posts
    sentiment_counts = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    if recent:
        results = analyze_sentiment(recent)
        for r in results:
            sentiment_counts[r['label']] += 1

    # Alert: negative sentiment spike
    total = max(sum(sentiment_counts.values()), 1)
    neg_pct = round((sentiment_counts['Negative'] / total) * 100, 1)

    alerts = []
    if neg_pct >= 40:
        alerts.append({
            'level': 'danger',
            'icon': '🚨',
            'message': f'High negative sentiment detected! {neg_pct}% of recent posts are negative.',
        })
    elif neg_pct >= 25:
        alerts.append({
            'level': 'warning',
            'icon': '⚠️',
            'message': f'Elevated negative sentiment: {neg_pct}% of recent posts.',
        })
    else:
        alerts.append({
            'level': 'success',
            'icon': '✅',
            'message': f'Sentiment is healthy. Only {neg_pct}% negative posts.',
        })

    # Engagement spike detection
    if len(posts) >= 10:
        avg_likes = sum(p.likes or 0 for p in posts) / len(posts)
        top_posts = [p for p in recent if (p.likes or 0) > avg_likes * 2]
        if top_posts:
            alerts.append({
                'level': 'info',
                'icon': '🔥',
                'message': f'{len(top_posts)} posts are getting 2x more likes than average!',
            })

    # Hourly post volume (last 12 hours)
    hourly = defaultdict(int)
    for post in posts[-50:]:
        if post.created_at:
            hour_key = post.created_at.strftime('%H:00')
            hourly[hour_key] += 1

    hourly_labels = sorted(hourly.keys())

    # Live feed: most recent 10 posts
    live_feed = []
    for post in sorted(posts, key=lambda p: p.created_at or datetime.min, reverse=True)[:10]:
        live_feed.append({
            'author': post.author or 'Unknown',
            'text': (post.text or '')[:100] + '...' if len(post.text or '') > 100 else post.text or '',
            'likes': post.likes or 0,
            'time': post.created_at.strftime('%H:%M') if post.created_at else '—',
        })

    return {
        'recent_count': len(recent),
        'total_posts': len(posts),
        'sentiment': sentiment_counts,
        'neg_pct': neg_pct,
        'alerts': alerts,
        'hourly_labels': hourly_labels,
        'hourly_counts': [hourly[h] for h in hourly_labels],
        'live_feed': live_feed,
        'last_updated': datetime.utcnow().strftime('%d %b %Y, %H:%M UTC'),
    }
