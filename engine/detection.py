"""
MullBar — Detection Engine (OPTIMIZED)
Implements cycle detection, smurfing detection, and shell network detection.
Optimized for large datasets (10K+ transactions).
"""

import networkx as nx
import pandas as pd
from datetime import timedelta
from collections import defaultdict


# ─────────────────────────────────────────────
#  CYCLE DETECTION  (length 3–5, bounded DFS)
# ─────────────────────────────────────────────

def detect_cycles(G: nx.DiGraph, min_len: int = 3, max_len: int = 5, max_results: int = 50) -> list[dict]:
    """
    Detect circular fund routing (cycles of length 3–5).
    Uses SCC pruning first, then bounded DFS within each SCC.
    Only keeps cycles where edges have been used multiple times (frequency ≥ 2).
    """
    rings = []
    seen_cycles = set()

    # SCC pruning: only search for cycles within strongly connected components
    sccs = [scc for scc in nx.strongly_connected_components(G) if len(scc) >= min_len]

    for scc in sccs:
        if len(rings) >= max_results:
            break

        subgraph = G.subgraph(scc)

        try:
            for cycle in nx.simple_cycles(subgraph, length_bound=max_len):
                if len(rings) >= max_results:
                    break
                if len(cycle) < min_len:
                    continue
                cycle_key = tuple(sorted(cycle))
                if cycle_key in seen_cycles:
                    continue
                seen_cycles.add(cycle_key)

                total_flow = _cycle_flow(G, cycle)
                frequency = _cycle_frequency(G, cycle)

                if frequency < len(cycle) * 2:
                    continue

                rings.append({
                    "members": list(cycle),
                    "pattern_type": "cycle",
                    "cycle_length": len(cycle),
                    "total_flow": total_flow,
                    "cycle_frequency": frequency,
                    "pattern_label": f"cycle_length_{len(cycle)}",
                })
        except Exception:
            # Fallback to bounded DFS within this SCC
            for r in _dfs_cycle_detection(subgraph, min_len, max_len):
                if len(rings) >= max_results:
                    break
                cycle_key = tuple(sorted(r["members"]))
                if cycle_key not in seen_cycles:
                    seen_cycles.add(cycle_key)
                    rings.append(r)

    return rings


def _cycle_flow(G: nx.DiGraph, cycle: list) -> float:
    """Total flow through a cycle."""
    total = 0.0
    for i in range(len(cycle)):
        src, dst = cycle[i], cycle[(i + 1) % len(cycle)]
        if G.has_edge(src, dst):
            total += G[src][dst]["total_amount"]
    return round(total, 2)


def _cycle_frequency(G: nx.DiGraph, cycle: list) -> int:
    """Total number of transactions across all edges in the cycle."""
    total = 0
    for i in range(len(cycle)):
        src, dst = cycle[i], cycle[(i + 1) % len(cycle)]
        if G.has_edge(src, dst):
            total += G[src][dst]["count"]
    return total


def _dfs_cycle_detection(G: nx.DiGraph, min_len: int, max_len: int) -> list[dict]:
    """Fallback bounded DFS cycle detection."""
    rings = []
    seen = set()

    def dfs(node, path, visited):
        if len(path) > max_len:
            return
        for neighbor in G.successors(node):
            if neighbor == path[0] and len(path) >= min_len:
                cycle_key = tuple(sorted(path))
                if cycle_key not in seen:
                    seen.add(cycle_key)
                    rings.append({
                        "members": list(path),
                        "pattern_type": "cycle",
                        "cycle_length": len(path),
                        "total_flow": _cycle_flow(G, path),
                        "cycle_frequency": _cycle_frequency(G, path),
                        "pattern_label": f"cycle_length_{len(path)}",
                    })
            elif neighbor not in visited and len(path) < max_len:
                visited.add(neighbor)
                dfs(neighbor, path + [neighbor], visited)
                visited.discard(neighbor)

    for node in G.nodes():
        dfs(node, [node], {node})

    return rings


# ─────────────────────────────────────────────
#  SMURFING DETECTION  (fan-in / fan-out)
#  OPTIMIZED: pre-grouped DataFrames + two-pointer window
# ─────────────────────────────────────────────

def detect_smurfing(
    G: nx.DiGraph, df: pd.DataFrame, threshold: int = 10, window_hours: int = 72
) -> list[dict]:
    """
    Detect smurfing patterns with sliding 72-hour window.
    Fan-in:  ≥threshold senders  → 1 receiver within window
    Fan-out: 1 sender → ≥threshold receivers within window
    """
    rings = []
    df_ts = df.copy()
    df_ts["timestamp"] = pd.to_datetime(df_ts["timestamp"])
    window = timedelta(hours=window_hours)

    # Pre-group by receiver and sender for fast lookup
    recv_groups = {name: group.sort_values("timestamp") for name, group in df_ts.groupby("receiver_id")}
    send_groups = {name: group.sort_values("timestamp") for name, group in df_ts.groupby("sender_id")}

    # --- Fan-in ---
    for node in G.nodes():
        if G.in_degree(node) < threshold:
            continue
        incoming = recv_groups.get(node)
        if incoming is None or incoming.empty:
            continue

        best = _best_window_fast(incoming, "sender_id", window, threshold)
        if best is not None:
            w_txns, unique_count = best
            members = list(w_txns["sender_id"].unique()) + [node]
            velocity = len(w_txns) / (window_hours / 24)
            rings.append({
                "members": members,
                "pattern_type": "fan_in",
                "aggregator": node,
                "sender_count": unique_count,
                "total_amount": round(float(w_txns["amount"].sum()), 2),
                "velocity": round(velocity, 2),
                "pattern_label": "fan_in_smurfing",
            })

    # --- Fan-out ---
    for node in G.nodes():
        if G.out_degree(node) < threshold:
            continue
        outgoing = send_groups.get(node)
        if outgoing is None or outgoing.empty:
            continue

        best = _best_window_fast(outgoing, "receiver_id", window, threshold)
        if best is not None:
            w_txns, unique_count = best
            members = [node] + list(w_txns["receiver_id"].unique())
            velocity = len(w_txns) / (window_hours / 24)
            rings.append({
                "members": members,
                "pattern_type": "fan_out",
                "disperser": node,
                "receiver_count": unique_count,
                "total_amount": round(float(w_txns["amount"].sum()), 2),
                "velocity": round(velocity, 2),
                "pattern_label": "fan_out_smurfing",
            })

    return rings


def _best_window_fast(txns: pd.DataFrame, count_col: str, window, threshold: int):
    """
    Find the densest sliding window meeting the threshold.
    Uses two-pointer approach instead of O(n²) scan.
    """
    timestamps = txns["timestamp"].values  # numpy datetime64
    counterparties = txns[count_col].values
    n = len(timestamps)
    if n == 0:
        return None

    # Convert timedelta to numpy timedelta64 for comparison
    window_ns = pd.Timedelta(window).to_timedelta64()

    best_result = None
    best_count = 0
    left = 0

    # Track unique counterparties in current window
    cp_counter = defaultdict(int)
    unique_count = 0

    for right in range(n):
        # Add right element
        cp = counterparties[right]
        cp_counter[cp] += 1
        if cp_counter[cp] == 1:
            unique_count += 1

        # Shrink window from left if too wide
        while timestamps[right] - timestamps[left] > window_ns:
            lcp = counterparties[left]
            cp_counter[lcp] -= 1
            if cp_counter[lcp] == 0:
                unique_count -= 1
                del cp_counter[lcp]
            left += 1

        # Check if this window meets threshold
        if unique_count >= threshold and unique_count > best_count:
            best_count = unique_count
            best_result = (txns.iloc[left:right + 1], unique_count)

    return best_result


# ─────────────────────────────────────────────
#  SHELL NETWORK DETECTION (OPTIMIZED)
#  Pre-compute shell candidates, limit chain depth
# ─────────────────────────────────────────────

def detect_shell_networks(
    G: nx.DiGraph, min_hops: int = 3, max_txn_count: int = 3, max_results: int = 100
) -> list[dict]:
    """
    Detect layered shell networks.
    Chains ≥ min_hops with intermediary nodes having ≤ max_txn_count transactions.
    """
    rings = []
    seen_chains = set()

    # Identify shell candidates
    shell_candidates = set()
    for node in G.nodes():
        total_txns = G.in_degree(node) + G.out_degree(node)
        if 1 <= total_txns <= max_txn_count:
            shell_candidates.add(node)

    if not shell_candidates:
        return rings

    # Only start from non-shell nodes that have edges to shell nodes
    start_nodes = set()
    for shell in shell_candidates:
        for pred in G.predecessors(shell):
            if pred not in shell_candidates:
                start_nodes.add(pred)
        for succ in G.successors(shell):
            if succ not in shell_candidates:
                start_nodes.add(succ)

    for start_node in start_nodes:
        if len(rings) >= max_results:
            break
        _find_shell_chains(
            G, start_node, [], shell_candidates, min_hops, rings, seen_chains,
            max_depth=6, max_results=max_results
        )

    return rings


def _find_shell_chains(G, node, path, shell_candidates, min_hops, rings, seen_chains, max_depth=6, max_results=100):
    """Recursively find chains through shell accounts."""
    if len(rings) >= max_results:
        return

    path = path + [node]
    if len(path) > max_depth:
        return

    for successor in G.successors(node):
        if successor in path:
            continue
        if len(rings) >= max_results:
            return

        new_path = path + [successor]
        if len(new_path) >= min_hops + 2:
            intermediates = new_path[1:-1]
            shell_count = sum(1 for n in intermediates if n in shell_candidates)
            if shell_count >= 2 and len(intermediates) >= min_hops:
                chain_key = tuple(sorted(new_path))
                if chain_key not in seen_chains:
                    seen_chains.add(chain_key)
                    total_flow = sum(
                        G[new_path[i]][new_path[i + 1]]["total_amount"]
                        for i in range(len(new_path) - 1)
                        if G.has_edge(new_path[i], new_path[i + 1])
                    )
                    rings.append({
                        "members": new_path,
                        "pattern_type": "shell_network",
                        "chain_length": len(new_path),
                        "shell_accounts": [n for n in intermediates if n in shell_candidates],
                        "total_flow": round(total_flow, 2),
                        "pattern_label": "layered_shell_network",
                    })

        if successor in shell_candidates and len(new_path) < max_depth:
            _find_shell_chains(
                G, successor, path, shell_candidates, min_hops, rings, seen_chains, max_depth, max_results
            )
