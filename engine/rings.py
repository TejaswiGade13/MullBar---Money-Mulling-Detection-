"""
MullBar — Fraud Ring Detection
Clusters suspicious nodes using connected components and assigns RING_### IDs.
"""

import networkx as nx
from collections import defaultdict


def assign_ring_ids(all_rings: list[dict]) -> list[dict]:
    """
    Assign sequential RING_### IDs to each detected ring.
    Modifies rings in-place and returns them.
    """
    for idx, ring in enumerate(all_rings):
        ring["ring_id"] = f"RING_{idx + 1:03d}"
    return all_rings


def aggregate_rings(
    G: nx.DiGraph, suspicious_accounts: dict, all_rings: list[dict]
) -> list[dict]:
    """
    Build connected-component fraud clusters from suspicious accounts.
    Each cluster becomes a fraud ring with averaged risk score.
    Returns the enriched all_rings list.
    """
    # Ring risk scores = average of member scores
    for ring in all_rings:
        member_scores = [
            suspicious_accounts.get(m, {}).get("suspicion_score", 0)
            for m in ring["members"]
        ]
        ring["risk_score"] = round(
            sum(member_scores) / max(len(member_scores), 1), 1
        )

    return all_rings
