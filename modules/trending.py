import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer


def extract_trending(posts):
    """Extract and rank hashtags by frequency."""
    hashtags = []
    for post in posts:
        text = post.text or ''
        tags = re.findall(r'#(\w+)', text)
        hashtags.extend([t.lower() for t in tags])

    counter = Counter(hashtags)
    return [{'tag': f'#{tag}', 'count': count}
            for tag, count in counter.most_common(20)]


def extract_keywords(posts):
    """Extract top keywords using TF-IDF."""
    texts = [post.text or '' for post in posts if post.text]

    if len(texts) < 2:
        # Fallback: simple word frequency
        words = []
        for post in posts:
            text = post.text or ''
            clean = re.sub(r'[^a-zA-Z\s]', '', text.lower())
            words.extend([w for w in clean.split()
                          if len(w) > 3 and w not in STOPWORDS])
        counter = Counter(words)
        return [{'word': word, 'score': count}
                for word, count in counter.most_common(20)]

    try:
        vectorizer = TfidfVectorizer(
            max_features=20,
            stop_words='english',
            ngram_range=(1, 2)
        )
        vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        scores = vectorizer.idf_

        keywords = sorted(
            zip(feature_names, scores),
            key=lambda x: x[1], reverse=True
        )
        return [{'word': word, 'score': round(float(score), 3)}
                for word, score in keywords[:20]]

    except Exception:
        return []


# Common stopwords to filter
STOPWORDS = {
    'this', 'that', 'with', 'have', 'from', 'they', 'will', 'been', 'were',
    'their', 'there', 'what', 'when', 'your', 'just', 'more', 'also', 'into',
    'some', 'than', 'then', 'them', 'these', 'those', 'http', 'https', 'www'
}
