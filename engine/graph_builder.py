"""
MullBar — Graph Builder
Constructs a directed transaction graph with edge and node attributes.
"""

import networkx as nx
import pandas as pd
from collections import defaultdict


def build_graph(df: pd.DataFrame) -> nx.DiGraph:
    """
    Build a directed graph from a transaction DataFrame.
    
    Edge attributes:  amount, timestamp, transaction_id (per-txn list)
    Node features:    in_degree, out_degree, transaction_count,
                      total_volume, unique_counterparties
    """
    G = nx.DiGraph()

    for _, row in df.iterrows():
        sender = row["sender_id"]
        receiver = row["receiver_id"]
        amount = float(row["amount"])
        ts = row["timestamp"]
        txn_id = row["transaction_id"]

        # Ensure nodes exist
        for nid in (sender, receiver):
            if nid not in G:
                G.add_node(
                    nid,
                    total_sent=0.0,
                    total_received=0.0,
                    send_timestamps=[],
                    recv_timestamps=[],
                    counterparties=set(),
                    transaction_ids=[],
                )

        # Edge: aggregate multiple transactions between same pair
        if G.has_edge(sender, receiver):
            edata = G[sender][receiver]
            edata["transactions"].append(
                {"amount": amount, "timestamp": ts, "transaction_id": txn_id}
            )
            edata["total_amount"] += amount
            edata["count"] += 1
        else:
            G.add_edge(
                sender,
                receiver,
                transactions=[{"amount": amount, "timestamp": ts, "transaction_id": txn_id}],
                total_amount=amount,
                count=1,
            )

        # Update node metadata
        G.nodes[sender]["total_sent"] += amount
        G.nodes[sender]["send_timestamps"].append(ts)
        G.nodes[sender]["counterparties"].add(receiver)
        G.nodes[sender]["transaction_ids"].append(txn_id)

        G.nodes[receiver]["total_received"] += amount
        G.nodes[receiver]["recv_timestamps"].append(ts)
        G.nodes[receiver]["counterparties"].add(sender)
        G.nodes[receiver]["transaction_ids"].append(txn_id)

    # Compute derived node features
    for nid in G.nodes():
        nd = G.nodes[nid]
        nd["in_degree"] = G.in_degree(nid)
        nd["out_degree"] = G.out_degree(nid)
        nd["transaction_count"] = len(nd["transaction_ids"])
        nd["total_volume"] = nd["total_sent"] + nd["total_received"]
        nd["unique_counterparties"] = len(nd["counterparties"])

    return G
