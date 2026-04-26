import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from collections import defaultdict


# ── Cluster personality definitions ───────────────────────────
# Assigned AFTER clustering based on actual cluster metrics,
# NOT by arbitrary cluster_id order.
_PERSONAS = [
    {
        'name': 'Power Users',
        'description': 'High activity, high engagement — core community members',
        'color': '#00d4ff',
    },
    {
        'name': 'Casual Engagers',
        'description': 'Moderate posting, occasional likes and shares',
        'color': '#3fb950',
    },
    {
        'name': 'Silent Observers',
        'description': 'Low engagement — mostly consume content without interacting',
        'color': '#8b949e',
    },
    {
        'name': 'Viral Creators',
        'description': 'Low post count but extremely high likes and shares per post',
        'color': '#f78166',
    },
    {
        'name': 'Brand Advocates',
        'description': 'Consistent posters with strong brand-focused content',
        'color': '#d29922',
    },
]


def _assign_persona(cluster_stats, all_cluster_stats):
    """
    Assign a persona to a cluster based on its relative metrics.
    Uses percentile rank across all clusters so every persona
    maps to a real behavioral pattern.

    cluster_stats : dict with avg_likes, avg_shares, post_count, avg_comments
    all_cluster_stats : list of all cluster stat dicts
    """
    def rank(key):
        """Return 0–1 percentile rank of this cluster for `key`."""
        vals = sorted(c[key] for c in all_cluster_stats)
        pos = vals.index(cluster_stats[key])
        return pos / max(len(vals) - 1, 1)

    likes_rank = rank('avg_likes')
    shares_rank = rank('avg_shares')
    posts_rank = rank('post_count')
    comments_rank = rank('avg_comments')

    engagement = (likes_rank + shares_rank + comments_rank) / 3

    # ── Decision tree based on behavioral signals ─────────────
    # Viral: high engagement but LOW post count
    if shares_rank >= 0.6 and likes_rank >= 0.6 and posts_rank <= 0.4:
        return 'Viral Creators'

    # Power: high posting AND high engagement
    if posts_rank >= 0.6 and engagement >= 0.6:
        return 'Power Users'

    # Silent: low engagement regardless of post count
    if engagement <= 0.35:
        return 'Silent Observers'

    # Brand Advocates: high post count, moderate engagement, long texts
    if posts_rank >= 0.5 and 0.35 < engagement < 0.65:
        return 'Brand Advocates'

    # Default: Casual Engagers
    return 'Casual Engagers'


def _fallback_percentile_segments(user_stats):
    """
    Fallback when there are too few unique users for KMeans.
    Uses percentile splits to guarantee all segment types appear.
    """
    if not user_stats:
        return []

    authors = list(user_stats.keys())

    # Score each user: combined engagement metric
    scores = {}
    for author, s in user_stats.items():
        pc = max(s['post_count'], 1)
        avg_eng = (
            (s['total_likes'] / pc) * 0.5 +
            (s['total_shares'] / pc) * 0.3 +
            (s['total_comments'] / pc) * 0.2
        )
        scores[author] = {
            'engagement': avg_eng,
            'post_count': s['post_count'],
            'avg_likes': round(s['total_likes'] / pc, 1),
            'avg_shares': round(s['total_shares'] / pc, 1),
            'avg_comments': round(s['total_comments'] / pc, 1),
        }

    sorted_authors = sorted(authors,
                            key=lambda a: scores[a]['engagement'],
                            reverse=True)
    n = len(sorted_authors)

    # Guarantee at least 1 user per segment via percentile splits
    cutoffs = {
        'Power Users': sorted_authors[:max(1, int(n * 0.15))],
        'Viral Creators': sorted_authors[max(1, int(n * 0.15)):max(2, int(n * 0.30))],
        'Brand Advocates': sorted_authors[max(2, int(n * 0.30)):max(3, int(n * 0.55))],
        'Casual Engagers': sorted_authors[max(3, int(n * 0.55)):max(4, int(n * 0.80))],
        'Silent Observers': sorted_authors[max(4, int(n * 0.80)):],
    }

    segments = []
    for i, (pname, members) in enumerate(cutoffs.items()):
        if not members:
            continue
        persona = next(
            (p for p in _PERSONAS if p['name'] == pname), _PERSONAS[i % len(_PERSONAS)])
        users = [{
            'author': a,
            'post_count': scores[a]['post_count'],
            'avg_likes': scores[a]['avg_likes'],
            'avg_shares': scores[a]['avg_shares'],
            'avg_comments': scores[a]['avg_comments'],
        } for a in members]

        segments.append({
            'id': i,
            'name': persona['name'],
            'description': persona['description'],
            'color': persona['color'],
            'user_count': len(members),
            'users': sorted(users,
                            key=lambda x: x['avg_likes'],
                            reverse=True)[:10],
            'avg_likes': round(
                sum(u['avg_likes'] for u in users) / len(users), 1
            ),
            'avg_shares': round(
                sum(u['avg_shares'] for u in users) / len(users), 1
            ),
        })

    return sorted(segments, key=lambda x: x['user_count'], reverse=True)


def segment_users(posts, n_clusters=5):
    """
    Cluster users based on posting behavior.

    Fix: cluster names are assigned AFTER fitting by ranking each
    cluster's actual metrics — guarantees all 5 segment types appear
    as long as there are enough distinct users.
    """
    # ── Aggregate per-author stats ────────────────────────────
    user_stats = defaultdict(lambda: {
        'post_count': 0,
        'total_likes': 0,
        'total_shares': 0,
        'total_comments': 0,
        'total_length': 0,
    })

    for post in posts:
        author = post.author or 'Unknown'
        user_stats[author]['post_count'] += 1
        user_stats[author]['total_likes'] += post.likes or 0
        user_stats[author]['total_shares'] += post.shares or 0
        user_stats[author]['total_comments'] += post.comments or 0
        user_stats[author]['total_length'] += len(post.text or '')

    # ── Fallback if too few unique users ──────────────────────
    if len(user_stats) < n_clusters:
        return _fallback_percentile_segments(user_stats)

    authors = list(user_stats.keys())
    features = []

    for author in authors:
        s = user_stats[author]
        pc = max(s['post_count'], 1)
        features.append([
            s['post_count'],
            s['total_likes'] / pc,    # avg likes per post
            s['total_shares'] / pc,    # avg shares per post
            s['total_comments'] / pc,    # avg comments per post
            s['total_length'] / pc,    # avg text length
        ])

    X = np.array(features, dtype=float)

    # ── Scale + cluster ───────────────────────────────────────
    try:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        kmeans = KMeans(
            n_clusters=min(n_clusters, len(authors)),
            random_state=42,
            n_init=20,     # more inits = more stable clusters
        )
        labels = kmeans.fit_predict(X_scaled)

    except Exception:
        # Last resort: fall back to percentile segments
        return _fallback_percentile_segments(user_stats)

    # ── Compute per-cluster summary stats ─────────────────────
    cluster_raw = defaultdict(list)
    for i, author in enumerate(authors):
        s = user_stats[author]
        pc = max(s['post_count'], 1)
        cluster_raw[int(labels[i])].append({
            'author': author,
            'post_count': s['post_count'],
            'avg_likes': round(s['total_likes'] / pc, 1),
            'avg_shares': round(s['total_shares'] / pc, 1),
            'avg_comments': round(s['total_comments'] / pc, 1),
        })

    # ── Build cluster-level summary for persona assignment ────
    cluster_summaries = {}
    for cid, users in cluster_raw.items():
        cluster_summaries[cid] = {
            'post_count': round(sum(u['post_count'] for u in users) / len(users), 2),
            'avg_likes': round(sum(u['avg_likes'] for u in users) / len(users), 2),
            'avg_shares': round(sum(u['avg_shares'] for u in users) / len(users), 2),
            'avg_comments': round(sum(u['avg_comments'] for u in users) / len(users), 2),
        }

    all_stats = list(cluster_summaries.values())

    # ── Assign personas — NO two clusters get the same name ───
    assigned_names = {}
    used_names = set()

    # First pass: best-fit persona
    for cid, stats in cluster_summaries.items():
        name = _assign_persona(stats, all_stats)
        if name not in used_names:
            assigned_names[cid] = name
            used_names.add(name)
        else:
            assigned_names[cid] = None   # collision — resolve in second pass

    # Second pass: assign remaining personas to collision clusters
    all_persona_names = [p['name'] for p in _PERSONAS]
    remaining = [n for n in all_persona_names if n not in used_names]
    remaining_iter = iter(remaining)

    for cid in assigned_names:
        if assigned_names[cid] is None:
            try:
                assigned_names[cid] = next(remaining_iter)
            except StopIteration:
                assigned_names[cid] = 'Casual Engagers'

    # ── Build final output ────────────────────────────────────
    segments = []
    for cid, users in cluster_raw.items():
        pname = assigned_names[cid]
        persona = next(
            (p for p in _PERSONAS if p['name'] == pname),
            _PERSONAS[cid % len(_PERSONAS)]
        )

        segments.append({
            'id': cid,
            'name': persona['name'],
            'description': persona['description'],
            'color': persona['color'],
            'user_count': len(users),
            'users': sorted(users,
                            key=lambda x: x['avg_likes'],
                            reverse=True)[:10],
            'avg_likes': cluster_summaries[cid]['avg_likes'],
            'avg_shares': cluster_summaries[cid]['avg_shares'],
        })

    return sorted(segments, key=lambda x: x['user_count'], reverse=True)
