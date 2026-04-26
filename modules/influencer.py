import networkx as nx
import re
from collections import defaultdict


def detect_influencers(posts):
    """Detect top influencers using Eigenvector Centrality + engagement metrics."""

    G = nx.DiGraph()   # Directed graph: author → mention

    # Build engagement stats per author
    author_stats = defaultdict(lambda: {
        'likes': 0,
        'shares': 0,
        'comments': 0,
        'posts': 0,
    })

    for post in posts:
        author = post.author or 'Unknown'
        text = post.text or ''
        mentions = re.findall(r'@(\w+)', text)

        author_stats[author]['likes'] += post.likes or 0
        author_stats[author]['shares'] += post.shares or 0
        author_stats[author]['comments'] += post.comments or 0
        author_stats[author]['posts'] += 1

        G.add_node(author)
        for mention in mentions:
            if mention != author:
                G.add_edge(author, mention)

    # Compute centrality
    try:
        if len(G.nodes) > 1:
            # Use undirected for eigenvector centrality
            UG = G.to_undirected()
            if nx.is_connected(UG):
                eigen_cent = nx.eigenvector_centrality(UG, max_iter=500)
            else:
                # Compute on largest component
                largest = max(nx.connected_components(UG), key=len)
                sub = UG.subgraph(largest)
                eigen_cent = nx.eigenvector_centrality(sub, max_iter=500)
                for node in UG.nodes:
                    if node not in eigen_cent:
                        eigen_cent[node] = 0.0
        else:
            eigen_cent = {n: 0.0 for n in G.nodes}

        degree_cent = nx.degree_centrality(G)

    except Exception:
        eigen_cent = {n: 0.0 for n in G.nodes}
        degree_cent = {n: 0.0 for n in G.nodes}

    # Compute composite influence score
    influencers = []

    for author, stats in author_stats.items():
        pc = max(stats['posts'], 1)

        engagement_score = (
            stats['likes'] * 1.0 +
            stats['shares'] * 2.0 +
            stats['comments'] * 1.5
        ) / pc

        network_score = (eigen_cent.get(author, 0) * 50 +
                         degree_cent.get(author, 0) * 50)

        influence_score = round(
            (engagement_score * 0.6) + (network_score * 0.4), 2
        )

        influencers.append({
            'rank': 0,
            'author': author,
            'posts': stats['posts'],
            'total_likes': stats['likes'],
            'total_shares': stats['shares'],
            'total_comments': stats['comments'],
            'avg_engagement': round(engagement_score, 1),
            'eigen_score': round(eigen_cent.get(author, 0), 4),
            'degree_score': round(degree_cent.get(author, 0), 4),
            'influence_score': influence_score,
        })

    # Sort by influence score
    influencers.sort(key=lambda x: x['influence_score'], reverse=True)

    # Assign ranks
    for i, inf in enumerate(influencers):
        inf['rank'] = i + 1

    return influencers[:20]
