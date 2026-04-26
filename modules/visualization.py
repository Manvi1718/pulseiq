from collections import defaultdict
from datetime import datetime


def get_visualization_data(posts):
    """Prepare all chart data for the visualization module."""

    if not posts:
        return {}

    # ── Engagement Over Time ──────────────────────────────────
    daily = defaultdict(
        lambda: {'likes': 0, 'shares': 0, 'comments': 0, 'posts': 0})

    for post in posts:
        date_key = post.created_at.strftime(
            '%Y-%m-%d') if post.created_at else 'Unknown'
        daily[date_key]['likes'] += post.likes or 0
        daily[date_key]['shares'] += post.shares or 0
        daily[date_key]['comments'] += post.comments or 0
        daily[date_key]['posts'] += 1

    sorted_dates = sorted(daily.keys())

    timeline = {
        'labels': sorted_dates,
        'likes': [daily[d]['likes'] for d in sorted_dates],
        'shares': [daily[d]['shares'] for d in sorted_dates],
        'comments': [daily[d]['comments'] for d in sorted_dates],
        'posts': [daily[d]['posts'] for d in sorted_dates],
    }

    # ── Top Authors by Engagement ─────────────────────────────
    author_eng = defaultdict(lambda: {'likes': 0, 'shares': 0, 'posts': 0})
    for post in posts:
        a = post.author or 'Unknown'
        author_eng[a]['likes'] += post.likes or 0
        author_eng[a]['shares'] += post.shares or 0
        author_eng[a]['posts'] += 1

    top_authors = sorted(
        author_eng.items(),
        key=lambda x: x[1]['likes'] + x[1]['shares'],
        reverse=True
    )[:10]

    authors_chart = {
        'labels': [a[0][:15] for a in top_authors],
        'likes': [a[1]['likes'] for a in top_authors],
        'shares': [a[1]['shares'] for a in top_authors],
    }

    # ── Post Length vs Likes Scatter ──────────────────────────
    scatter = [
        {
            'x': len(post.text or ''),
            'y': post.likes or 0,
        }
        for post in posts if post.text
    ]

    # ── Hourly Activity ───────────────────────────────────────
    hourly = defaultdict(int)
    for post in posts:
        hour = post.created_at.hour if post.created_at else 0
        hourly[hour] += 1

    hourly_chart = {
        'labels': [f'{h:02d}:00' for h in range(24)],
        'counts': [hourly[h] for h in range(24)],
    }

    # ── Weekday Activity ──────────────────────────────────────
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    weekday_data = defaultdict(int)
    for post in posts:
        if post.created_at:
            weekday_data[post.created_at.weekday()] += 1

    weekday_chart = {
        'labels': weekdays,
        'counts': [weekday_data[i] for i in range(7)],
    }

    # ── Summary KPIs ─────────────────────────────────────────
    total_likes = sum(p.likes or 0 for p in posts)
    total_shares = sum(p.shares or 0 for p in posts)
    total_comments = sum(p.comments or 0 for p in posts)
    n = max(len(posts), 1)

    summary = {
        'total_posts': len(posts),
        'total_likes': total_likes,
        'total_shares': total_shares,
        'total_comments': total_comments,
        'avg_likes': round(total_likes / n, 1),
        'avg_shares': round(total_shares / n, 1),
        'avg_comments': round(total_comments / n, 1),
        'total_engagement': total_likes + total_shares + total_comments,
        'top_post_likes': max((p.likes or 0 for p in posts), default=0),
    }

    return {
        'timeline': timeline,
        'authors_chart': authors_chart,
        'scatter': scatter,
        'hourly': hourly_chart,
        'weekday': weekday_chart,
        'summary': summary,
    }
