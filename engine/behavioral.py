"""
MullBar — Behavioral Metrics
Computes volume anomaly, counterparty diversity, and circular flow ratio.
"""

import networkx as nx
import numpy as np


def compute_behavioral_features(G: nx.DiGraph) -> dict:
    """
    Compute behavioral features for every node.
    Returns dict: account_id -> {volume_anomaly, counterparty_diversity, circular_flow_ratio}
    """
    # Dataset-wide median volume
    volumes = [G.nodes[n]["total_volume"] for n in G.nodes()]
    median_volume = float(np.median(volumes)) if volumes else 1.0

    results = {}

    for node in G.nodes():
        nd = G.nodes[node]
        vol = nd["total_volume"]

        # --- Volume anomaly vs dataset median ---
        # Ratio > 1 means above median; capped at 10
        volume_anomaly = min(vol / max(median_volume, 0.01), 10.0)

        # --- Counterparty diversity ---
        # Ratio of unique counterparties to total transactions
        txn_count = nd["transaction_count"]
        unique_cp = nd["unique_counterparties"]
        counterparty_diversity = unique_cp / max(txn_count, 1)

        # --- Circular flow ratio ---
        # What fraction of a node's volume circulates back to itself via 2-hop paths
        circular_flow = _compute_circular_flow(G, node)

        results[node] = {
            "volume_anomaly": round(volume_anomaly, 3),
            "counterparty_diversity": round(counterparty_diversity, 3),
            "circular_flow_ratio": round(circular_flow, 3),
        }

    return results


def _compute_circular_flow(G: nx.DiGraph, node: str) -> float:
    """
    Estimate circular flow ratio: fraction of outgoing volume that
    eventually returns within 2 hops.
    """
    total_out = G.nodes[node]["total_sent"]
    if total_out == 0:
        return 0.0

    return_flow = 0.0
    for successor in G.successors(node):
        if G.has_edge(successor, node):
            # Direct return: A -> B -> A
            return_flow += G[successor][node]["total_amount"]
        # 2-hop return: A -> B -> C -> A
        for hop2 in G.successors(successor):
            if hop2 != node and G.has_edge(hop2, node):
                return_flow += min(
                    G[node][successor]["total_amount"],
                    G[hop2][node]["total_amount"],
                )

    return min(return_flow / total_out, 1.0)
