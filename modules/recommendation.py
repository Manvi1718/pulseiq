from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def get_recommendations(posts, top_n=3):
    """
    Content-based filtering using TF-IDF + Cosine Similarity.
    For each post, find the top_n most similar posts.
    """

    if len(posts) < 3:
        return []

    texts = [post.text or '' for post in posts]
    authors = [post.author or 'Unknown' for post in posts]
    likes = [post.likes or 0 for post in posts]

    # Build TF-IDF matrix
    try:
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=500,
            ngram_range=(1, 2),
            min_df=1,
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
    except Exception:
        return []

    # Compute cosine similarity matrix
    sim_matrix = cosine_similarity(tfidf_matrix)

    recommendations = []

    # Only process first 10 posts to keep UI clean
    for i in range(min(len(posts), 10)):
        sim_scores = list(enumerate(sim_matrix[i]))

        # Sort by similarity, exclude self (index i)
        sim_scores = sorted(
            [(j, score) for j, score in sim_scores if j != i],
            key=lambda x: x[1],
            reverse=True
        )

        # Get top_n similar posts above threshold
        similar = []
        for j, score in sim_scores[:top_n]:
            if score >= 0.10:
                similar.append({
                    'author': authors[j],
                    'text': texts[j][:100] + '...'
                    if len(texts[j]) > 100 else texts[j],
                    'score': round(float(score), 3),
                    'likes': likes[j],
                })

        if similar:
            recommendations.append({
                'author': authors[i],
                'text': texts[i][:100] + '...'
                if len(texts[i]) > 100 else texts[i],
                'similar': similar,
            })

    return recommendations
