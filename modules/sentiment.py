from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def analyze_sentiment(posts):
    analyzer = SentimentIntensityAnalyzer()
    results = []

    for post in posts:
        text = post.text or ''
        score = analyzer.polarity_scores(text)

        if score['compound'] >= 0.05:
            label = 'Positive'
            color = '#3fb950'
        elif score['compound'] <= -0.05:
            label = 'Negative'
            color = '#f85149'
        else:
            label = 'Neutral'
            color = '#8b949e'

        results.append({
            'id': post.id,
            'text': text[:120] + '...' if len(text) > 120 else text,
            'author': post.author or 'Unknown',
            'label': label,
            'color': color,
            'score': round(score['compound'], 3),
            'positive': round(score['pos'], 3),
            'negative': round(score['neg'], 3),
            'neutral': round(score['neu'], 3),
            'likes': post.likes,
            'shares': post.shares,
        })

    # Sort by absolute score descending
    results.sort(key=lambda x: abs(x['score']), reverse=True)
    return results
