"""
MullBar — Graph Builder (OPTIMIZED)
Constructs a directed transaction graph using vectorized operations.
Replaces O(E) iteration with O(1) bulk operations.
"""

import networkx as nx
import pandas as pd


def build_graph(df: pd.DataFrame) -> nx.DiGraph:
    """
    Build a directed graph from a transaction DataFrame.
    
    Edge attributes:  total_amount, count
    Node features:    in_degree, out_degree, transaction_count,
                      total_volume, unique_counterparties, total_sent, total_received
    """
    # 1. Edge Aggregation (Vectorized)
    # Group by sender/receiver and sum amounts/counts
    edges = df.groupby(["sender_id", "receiver_id"], as_index=False).agg(
        total_amount=("amount", "sum"),
        count=("amount", "count")
    )
    
    # 2. Build Graph from Edgelist (Fast C-level build)
    G = nx.from_pandas_edgelist(
        edges,
        source="sender_id",
        target="receiver_id",
        edge_attr=["total_amount", "count"],
        create_using=nx.DiGraph()
    )
    
    # 3. Node Aggregation (Vectorized Stats)
    # Sender stats
    sent_stats = df.groupby("sender_id").agg(
        total_sent=("amount", "sum"),
        sent_count=("amount", "count")
    ).to_dict("index")
    
    # Receiver stats
    recv_stats = df.groupby("receiver_id").agg(
        total_received=("amount", "sum"),
        recv_count=("amount", "count")
    ).to_dict("index")
    
    # 4. Set Node Attributes (Bulk)
    # We iterate nodes once to combine stats. This is O(N), much faster than O(E).
    node_attrs = {}
    for node in G.nodes():
        s = sent_stats.get(node, {})
        r = recv_stats.get(node, {})
        
        total_sent = float(s.get("total_sent", 0.0))
        total_received = float(r.get("total_received", 0.0))
        
        # Calculate unique counterparties using graph topology (fastest)
        # Using set(successors) | set(predecessors)
        # Note: G.degree() is sum of in+out edges, but doesn't handle unique across both.
        # But we can validly approximate or compute exactly.
        # Let's compute exactly using graph structure.
        succ = list(G.successors(node))
        pred = list(G.predecessors(node))
        unique_cp = len(set(succ + pred))
        
        node_attrs[node] = {
            "total_sent": total_sent,
            "total_received": total_received,
            "total_volume": total_sent + total_received,
            "transaction_count": s.get("sent_count", 0) + r.get("recv_count", 0),
            "unique_counterparties": unique_cp,
            # Degrees are updated automatically by nx, but we store them as attributes for export
            "in_degree": G.in_degree(node),
            "out_degree": G.out_degree(node),
        }
        
    nx.set_node_attributes(G, node_attrs)

    return G
