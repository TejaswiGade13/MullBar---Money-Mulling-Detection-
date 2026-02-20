"""
MullBar — Visualization Data Builder
Generates Cytoscape.js-compatible graph data with suspicion metadata.
"""

import networkx as nx
from collections import defaultdict


def build_viz_data(
    G: nx.DiGraph,
    suspicious_accounts: dict,
    all_rings: list[dict],
    explanations: dict,
) -> dict:
    """
    Build Cytoscape.js-compatible graph data.
    Returns {"nodes": [...], "edges": [...]}
    """
    nodes = []
    edges = []

    # Build ring membership lookup for coloring
    ring_membership = defaultdict(list)
    for ring in all_rings:
        ring_id = ring.get("ring_id", "unknown")
        for member in ring["members"]:
            if ring_id not in [r["ring_id"] for r in ring_membership[member]]:
                ring_membership[member].append({
                    "ring_id": ring_id,
                    "pattern": ring["pattern_type"],
                })

    for node_id in G.nodes():
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

    for src, dst, data in G.edges(data=True):
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
