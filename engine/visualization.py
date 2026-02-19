"""
MullBar — Visualization Data Builder (OPTIMIZED)
Generates Cytoscape.js-compatible graph data.
For large graphs, only includes suspicious nodes + their direct neighbors
to keep the browser responsive.
"""

import networkx as nx
from collections import defaultdict

# Max nodes to send to browser before filtering kicks in
MAX_VIZ_NODES = 150


def build_viz_data(
    G: nx.DiGraph,
    suspicious_accounts: dict,
    all_rings: list[dict],
    explanations: dict,
) -> dict:
    """
    Build Cytoscape.js-compatible graph data.
    For large graphs (>MAX_VIZ_NODES), only includes suspicious accounts
    and their direct neighbors to keep the frontend responsive.
    Returns {"nodes": [...], "edges": [...]}
    """
    # Decide which nodes to include
    total_nodes = G.number_of_nodes()
    if total_nodes > MAX_VIZ_NODES:
        visible_nodes = _select_visible_nodes(G, suspicious_accounts)
    else:
        visible_nodes = set(G.nodes())

    # Build ring membership lookup
    ring_membership = defaultdict(list)
    for ring in all_rings:
        ring_id = ring.get("ring_id", "unknown")
        ring_ids_seen = set()
        for member in ring["members"]:
            key = (member, ring_id)
            if key not in ring_ids_seen:
                ring_ids_seen.add(key)
                ring_membership[member].append({
                    "ring_id": ring_id,
                    "pattern": ring["pattern_type"],
                })

    nodes = []
    for node_id in visible_nodes:
        if node_id not in G.nodes():
            continue
        nd = G.nodes[node_id]
        account = suspicious_accounts.get(node_id)
        is_suspicious = account is not None
        score = account["suspicion_score"] if account else 0
        patterns = account.get("detected_patterns", []) if account else []
        rings_info = ring_membership.get(node_id, [])
        explanation = explanations.get(node_id, {})

        nodes.append({
            "data": {
                "id": node_id,
                "label": node_id,
                "suspicious": is_suspicious,
                "score": score,
                "patterns": patterns,
                "rings": rings_info,
                "total_sent": round(nd.get("total_sent", 0), 2),
                "total_received": round(nd.get("total_received", 0), 2),
                "total_volume": round(nd.get("total_volume", 0), 2),
                "in_degree": nd.get("in_degree", 0),
                "out_degree": nd.get("out_degree", 0),
                "unique_counterparties": nd.get("unique_counterparties", 0),
                "transaction_count": nd.get("transaction_count", 0),
                "why_flagged": explanation.get("why_flagged", ""),
                "risk_breakdown": explanation.get("risk_breakdown", []),
                "transaction_summary": explanation.get("transaction_summary", {}),
            }
        })

    # Only include edges between visible nodes
    edges = []
    for src, dst, data in G.edges(data=True):
        if src in visible_nodes and dst in visible_nodes:
            edges.append({
                "data": {
                    "source": src,
                    "target": dst,
                    "amount": round(data.get("total_amount", 0), 2),
                    "count": data.get("count", 1),
                    "label": f"${data.get('total_amount', 0):,.0f}",
                }
            })

    return {"nodes": nodes, "edges": edges}


def _select_visible_nodes(G: nx.DiGraph, suspicious_accounts: dict) -> set:
    """
    Select nodes to visualize: all suspicious accounts + their direct neighbors.
    If still too many, prioritize by risk score and limit neighbors.
    """
    suspicious_ids = set(suspicious_accounts.keys())
    visible = set(suspicious_ids)

    # Sort suspicious accounts by score (highest first)
    sorted_accounts = sorted(
        suspicious_accounts.items(),
        key=lambda x: x[1]["suspicion_score"],
        reverse=True,
    )

    # Add direct neighbors of suspicious accounts (limit per account)
    max_neighbors_per_node = max(3, 30 // max(len(suspicious_ids), 1))
    for account_id, _ in sorted_accounts:
        if len(visible) >= MAX_VIZ_NODES:
            break
        neighbors = list(G.predecessors(account_id)) + list(G.successors(account_id))
        for neighbor in neighbors[:max_neighbors_per_node]:
            visible.add(neighbor)
            if len(visible) >= MAX_VIZ_NODES:
                break

    return visible
