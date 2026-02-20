"""
MullBar — False Positive Control
Filters out legitimate high-volume accounts (merchants, payroll).
"""

import networkx as nx
import pandas as pd
from collections import Counter


def filter_false_positives(
    G: nx.DiGraph,
    suspicious_accounts: dict,
    df: pd.DataFrame,
    all_rings: list[dict],
) -> tuple[dict, set]:
    """
    Filter out accounts with high volume + high counterparty diversity + no structural anomalies.
    Returns (filtered_accounts, removed_ring_ids)
    """
    filtered = {}
    fp_accounts = set()
    df_copy = df.copy()
    df_copy["timestamp"] = pd.to_datetime(df_copy["timestamp"])

    for account_id, account_data in suspicious_accounts.items():
        account_txns = df_copy[
            (df_copy["sender_id"] == account_id) | (df_copy["receiver_id"] == account_id)
        ]

        if account_txns.empty:
            filtered[account_id] = account_data
            continue

        is_merchant = _is_likely_merchant(G, account_id, account_txns)
        is_payroll = _is_likely_payroll(G, account_id, account_txns)

        # Rule: don't flag accounts with high volume + high counterparty diversity + no structural anomalies
        has_structural = _has_structural_anomaly(account_data)

        if (is_merchant or is_payroll) and not has_structural:
            fp_accounts.add(account_id)
        else:
            filtered[account_id] = account_data

    # Remove rings where the hub node is a false positive
    removed_ring_ids = set()
    for ring in all_rings:
        hub = None
        if ring["pattern_type"] == "fan_in":
            hub = ring.get("aggregator")
        elif ring["pattern_type"] == "fan_out":
            hub = ring.get("disperser")

        if hub and hub in fp_accounts:
            removed_ring_ids.add(ring.get("ring_id", ""))

    # Remove accounts only in removed rings
    for account_id in list(filtered.keys()):
        data = filtered[account_id]
        remaining = [r for r in data.get("ring_ids", []) if r not in removed_ring_ids]
        if not remaining:
            del filtered[account_id]
        else:
            data["ring_ids"] = remaining

    return filtered, removed_ring_ids


def _is_likely_merchant(G, account_id, txns):
    """Merchant: many unique incoming senders, diverse amounts, long time span."""
    incoming = txns[txns["receiver_id"] == account_id]
    if len(incoming) < 15:
        return False

    unique_senders = incoming["sender_id"].nunique()
    amount_std = incoming["amount"].std() if len(incoming) > 1 else 0

    if unique_senders >= 10 and amount_std > 20:
        time_span = (incoming["timestamp"].max() - incoming["timestamp"].min()).days
        if time_span >= 5:
            return True
    return False


def _is_likely_payroll(G, account_id, txns):
    """Payroll: regular same-amount transfers to many recipients."""
    outgoing = txns[txns["sender_id"] == account_id]
    if len(outgoing) < 8:
        return False

    out_degree = G.out_degree(account_id)
    amounts = outgoing["amount"].round(2).values
    amount_counts = Counter(amounts)
    _, most_common_count = amount_counts.most_common(1)[0]

    uniformity = most_common_count / len(outgoing)
    if uniformity >= 0.6 and out_degree >= 8:
        return True

    unique_amounts = len(set(amounts))
    if unique_amounts <= 3 and len(outgoing) >= 10:
        return True

    return False


def _has_structural_anomaly(account_data: dict) -> bool:
    """Check if the account has genuine structural anomalies (cycles, shells)."""
    patterns = account_data.get("detected_patterns", [])
    structural_patterns = {"cycle_length_3", "cycle_length_4", "cycle_length_5", "layered_shell_network"}
    return bool(set(patterns) & structural_patterns)
