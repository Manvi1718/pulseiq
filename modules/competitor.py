from collections import Counter
import re


def _extract_hashtags(posts, exclude_keywords=None):
    """
    Extract hashtags, excluding any tag that contains a rival brand name.
    exclude_keywords: list of strings to block (e.g. ['nasa', 'bmw'])
    """
    hashtags = []
    exclude = [k.lower().strip() for k in (exclude_keywords or []) if k]

    for post in posts:
        tags = re.findall(r'#(\w+)', post.text or '')
        for t in tags:
            tag = t.lower()
            # Block hashtags that contain the rival brand name
            if any(ex in tag for ex in exclude):
                continue
            hashtags.append(tag)

    return hashtags


def compare_competitors(posts_a, posts_b,
                        name_a='Brand A', name_b='Brand B'):
    """
    Compare two sets of posts side-by-side.
    Each brand's hashtags exclude the rival brand name to prevent
    cross-contamination (e.g. #nasa appearing in BMW's top hashtags).
    """

    def compute_stats(posts, name, rival_name=None):
        if not posts:
            return {
                'name': name,
                'post_count': 0,
                'total_likes': 0,
                'total_shares': 0,
                'total_comments': 0,
                'avg_likes': 0,
                'avg_shares': 0,
                'avg_engagement': 0,
                'top_hashtags': [],
                'unique_authors': 0,
                'no_data': True,
            }

        n = max(len(posts), 1)
        total_likes = sum(p.likes or 0 for p in posts)
        total_shares = sum(p.shares or 0 for p in posts)
        total_comments = sum(p.comments or 0 for p in posts)

        # ── Exclude rival brand from hashtag list ──────────────
        exclude = [rival_name] if rival_name else []
        hashtags = _extract_hashtags(posts, exclude_keywords=exclude)
        top_tags = Counter(hashtags).most_common(5)

        return {
            'name': name,
            'post_count': len(posts),
            'total_likes': total_likes,
            'total_shares': total_shares,
            'total_comments': total_comments,
            'avg_likes': round(total_likes / n, 1),
            'avg_shares': round(total_shares / n, 1),
            'avg_engagement': round(
                (total_likes + total_shares + total_comments) / n, 1
            ),
            'top_hashtags': [
                {'tag': f'#{t}', 'count': c} for t, c in top_tags
            ],
            'unique_authors': len(
                set(p.author for p in posts if p.author)
            ),
            'no_data': False,
        }

    # Each brand excludes the other brand's name from hashtags
    stats_a = compute_stats(posts_a, name_a, rival_name=name_b)
    stats_b = compute_stats(posts_b, name_b, rival_name=name_a)

    def winner(val_a, val_b, label_a, label_b):
        if val_a > val_b:
            return label_a
        elif val_b > val_a:
            return label_b
        else:
            return 'Tie'

    return {
        'stats_a': stats_a,
        'stats_b': stats_b,
        'winners': {
            'posts': winner(stats_a['post_count'],
                            stats_b['post_count'],      name_a, name_b),
            'likes': winner(stats_a['avg_likes'],
                            stats_b['avg_likes'],       name_a, name_b),
            'shares': winner(stats_a['avg_shares'],
                             stats_b['avg_shares'],      name_a, name_b),
            'engagement': winner(stats_a['avg_engagement'],
                                 stats_b['avg_engagement'],  name_a, name_b),
            'reach': winner(stats_a['unique_authors'],
                            stats_b['unique_authors'],  name_a, name_b),
        },
        'chart_labels': ['Post Count', 'Avg Likes',
                         'Avg Shares', 'Avg Engagement',
                         'Unique Authors'],
        'chart_a': [
            stats_a['post_count'],  stats_a['avg_likes'],
            stats_a['avg_shares'],  stats_a['avg_engagement'],
            stats_a['unique_authors'],
        ],
        'chart_b': [
            stats_b['post_count'],  stats_b['avg_likes'],
            stats_b['avg_shares'],  stats_b['avg_engagement'],
            stats_b['unique_authors'],
        ],
    }
