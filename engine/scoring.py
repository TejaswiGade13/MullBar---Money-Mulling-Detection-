"""
MullBar — Composite Risk Scoring Engine
Explainable weighted score normalized to 0–100.

Weight allocation:
  30%  cycle involvement
  20%  smurfing
  15%  shell network
  15%  velocity
  10%  volume anomaly
  10%  circular flow
"""

import networkx as nx
from collections import defaultdict


WEIGHTS = {
    "cycle":          0.30,
    "smurfing":       0.20,
    "shell_network":  0.15,
    "velocity":       0.15,
    "volume_anomaly": 0.10,
    "circular_flow":  0.10,
}


def compute_composite_scores(
    G: nx.DiGraph,
    all_rings: list[dict],
    temporal_features: dict,
    behavioral_features: dict,
) -> dict:
    """
    Compute composite risk score (0–100) for every node involved in detections.
    Returns dict: account_id -> {
        suspicion_score, factor_scores, detected_patterns, ring_ids
    }
    """
    # --- Step 1: Compute raw factor scores per account ---
    factor_scores = defaultdict(lambda: {
        "cycle": 0.0,
        "smurfing": 0.0,
        "shell_network": 0.0,
        "velocity": 0.0,
        "volume_anomaly": 0.0,
        "circular_flow": 0.0,
    })
    detected_patterns = defaultdict(list)
    ring_ids = defaultdict(list)

    # Pattern-based factors from rings
    for ring in all_rings:
        ring_id = ring.get("ring_id", "RING_000")
        pattern = ring["pattern_type"]
        members = ring["members"]

        for member in members:
            if ring_id not in ring_ids[member]:
                ring_ids[member].append(ring_id)

            label = ring.get("pattern_label", pattern)
            if label not in detected_patterns[member]:
                detected_patterns[member].append(label)

            if pattern == "cycle":
                # Score based on cycle length (shorter = more suspicious)
                cycle_len = ring.get("cycle_length", 3)
                score = 100 - (cycle_len - 3) * 15  # len3=100, len4=85, len5=70
                factor_scores[member]["cycle"] = max(
                    factor_scores[member]["cycle"], score
                )
            elif pattern in ("fan_in", "fan_out"):
                # Score based on unique counterparties in the window
                count = ring.get("sender_count", ring.get("receiver_count", 10))
                score = min(100, count * 8)
                factor_scores[member]["smurfing"] = max(
                    factor_scores[member]["smurfing"], score
                )
            elif pattern == "shell_network":
                chain_len = ring.get("chain_length", 3)
                score = min(100, chain_len * 20)
                factor_scores[member]["shell_network"] = max(
                    factor_scores[member]["shell_network"], score
                )

    # Only score accounts that appear in at least one ring
    all_involved = set(factor_scores.keys())

    # Temporal and behavioral factors for involved accounts
    if temporal_features:
        # Normalize velocity across involved accounts
        velocities = [temporal_features.get(a, {}).get("velocity", 0) for a in all_involved]
        max_vel = max(velocities) if velocities else 1
        for account in all_involved:
            tf = temporal_features.get(account, {})
            vel = tf.get("velocity", 0)
            burst = tf.get("burst_score", 0)
            # Combine velocity and burst
            vel_score = (vel / max(max_vel, 0.01)) * 60 + min(burst * 10, 40)
            factor_scores[account]["velocity"] = min(100, round(vel_score, 1))

    if behavioral_features:
        for account in all_involved:
            bf = behavioral_features.get(account, {})
            vol_anom = bf.get("volume_anomaly", 0)
            circ_flow = bf.get("circular_flow_ratio", 0)

            factor_scores[account]["volume_anomaly"] = min(100, round(vol_anom * 20, 1))
            factor_scores[account]["circular_flow"] = min(100, round(circ_flow * 100, 1))

    # --- Step 2: Compute weighted composite score ---
    results = {}
    for account in all_involved:
        fs = factor_scores[account]
        composite = sum(fs[k] * WEIGHTS[k] for k in WEIGHTS)
        composite = round(min(100.0, max(0.0, composite)), 1)

        # Multi-ring bonus
        n_rings = len(ring_ids[account])
        if n_rings > 1:
            composite = min(100.0, composite + n_rings * 3)

        results[account] = {
            "suspicion_score": composite,
            "factor_scores": {k: round(v, 1) for k, v in fs.items()},
            "detected_patterns": detected_patterns[account],
            "ring_ids": ring_ids[account],
        }

    return results
