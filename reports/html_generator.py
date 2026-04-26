from flask import render_template
from datetime import datetime
from scrapers.facebook_scraper import fetch_facebook_posts
import os


def generate_html_report(case, posts, results_data, output_path):
    """
    Generate a standalone HTML report with embedded Chart.js charts.
    """
    try:
        html_content = render_template(
            'reports/full_report.html',
            case=case,
            posts=posts,
            results=results_data,
            generated_at=datetime.utcnow().strftime('%d %B %Y, %H:%M UTC'),
            is_html_export=True,     # enables Chart.js in the template
        )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return True, output_path

    except Exception as e:
        return False, str(e)


def build_results_data(case, posts):
    """
    Collect results from ALL modules for a given case's posts.
    Returns a single dict passed into the report template.
    """
    from modules.sentiment import analyze_sentiment
    from modules.trending import extract_trending, extract_keywords
    from modules.influencer import detect_influencers
    from modules.fake_news import detect_fake_news
    from modules.segmentation import segment_users
    from modules.visualization import get_visualization_data
    from modules.prediction import predict_engagement
    from collections import Counter

    data = {}

    # Sentiment
    sentiment_results = analyze_sentiment(posts) if posts else []
    counts = Counter(r['label'] for r in sentiment_results)
    data['sentiment'] = {
        'results': sentiment_results[:10],
        'counts': dict(counts),
        'positive': counts.get('Positive', 0),
        'negative': counts.get('Negative', 0),
        'neutral': counts.get('Neutral',  0),
    }

    # Trending
    data['trending'] = {
        'hashtags': extract_trending(posts)[:10] if posts else [],
        'keywords': extract_keywords(posts)[:10] if posts else [],
    }

    # Influencers
    data['influencers'] = detect_influencers(posts)[:5] if posts else []

    # Fake news
    fake_results = detect_fake_news(posts) if posts else []
    fake_count = sum(1 for r in fake_results if r['label'] == 'Fake')
    data['fake_news'] = {
        'results': fake_results[:10],
        'fake_count': fake_count,
        'real_count': len(fake_results) - fake_count,
    }

    # Segments
    data['segments'] = segment_users(posts)[:4] if posts else []

    # Visualization summary
    data['visualization'] = get_visualization_data(posts) if posts else {}

    # Prediction
    pred = predict_engagement(posts) if posts and len(posts) >= 10 else {}
    data['prediction'] = pred

    # Post stats
    n = max(len(posts), 1)
    data['summary'] = {
        'total_posts': len(posts),
        'total_likes': sum(p.likes or 0 for p in posts),
        'total_shares': sum(p.shares or 0 for p in posts),
        'total_comments': sum(p.comments or 0 for p in posts),
        'avg_likes': round(sum(p.likes or 0 for p in posts) / n, 1),
        'avg_engagement': round(
            sum((p.likes or 0) + (p.shares or 0) + (p.comments or 0)
                for p in posts) / n, 1
        ),
    }

    return data
