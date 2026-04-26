import networkx as nx
import re
from collections import defaultdict


def build_network(posts):
    """Build a directed social graph from author → mention edges."""

    G = nx.DiGraph()
    author_stats = defaultdict(int)

    for post in posts:
        author = post.author or 'Unknown'
        text = post.text or ''
        mentions = re.findall(r'@(\w+)', text)

        author_stats[author] += 1
        G.add_node(author)

        for mention in mentions:
            if mention != author:
                G.add_edge(author, mention)

    if len(G.nodes) == 0:
        return {}, {}, []

    # Degree centrality
    degree_cent = nx.degree_centrality(G)

    # Communities on undirected version
    UG = G.to_undirected()
    try:
        from networkx.algorithms import community
        if nx.is_connected(UG):
            communities = list(community.greedy_modularity_communities(UG))
        else:
            communities = []
            for component in nx.connected_components(UG):
                sub = UG.subgraph(component)
                if len(sub) >= 3:
                    comms = community.greedy_modularity_communities(sub)
                    communities.extend(comms)
    except Exception:
        communities = []

    # Color nodes by community
    color_palette = [
        '#00d4ff', '#3fb950', '#f85149',
        '#d29922', '#bc8cff', '#ffa657',
    ]
    node_colors = {}
    for i, comm in enumerate(communities):
        color = color_palette[i % len(color_palette)]
        for node in comm:
            node_colors[node] = color

    # Build vis.js compatible data
    nodes_data = []
    for node in G.nodes():
        size = max(10, min(50, author_stats.get(node, 1) * 8))
        color = node_colors.get(node, '#8b949e')
        nodes_data.append({
            'id': node,
            'label': node[:15],
            'size': size,
            'color': color,
            'title': f'{node} — {author_stats.get(node, 0)} posts',
        })

    edges_data = [
        {'from': u, 'to': v}
        for u, v in G.edges()
    ]

    # Top nodes by degree
    top_nodes = sorted(
        degree_cent.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    stats = {
        'node_count': G.number_of_nodes(),
        'edge_count': G.number_of_edges(),
        'communities': len(communities),
        'density': round(nx.density(G), 4),
        'top_nodes': [
            {'name': n, 'score': round(s, 4)}
            for n, s in top_nodes
        ],
    }

    network_data = {
        'nodes': nodes_data,
        'edges': edges_data,
    }

    return stats, network_data, communities
