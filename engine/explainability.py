"""
MullBar — Explainability Engine
Generates human-readable explanations for why each account was flagged.
"""

import networkx as nx

FACTOR_DESCRIPTIONS = {
    "cycle": "Involved in circular fund routing (money flows in a loop)",
    "smurfing": "Participant in structured transaction splitting (many small transfers within 72h window)",
    "shell_network": "Part of a layered passthrough chain using shell accounts",
    "velocity": "Unusually high transaction frequency or burst activity",
    "volume_anomaly": "Transaction volume significantly deviates from dataset median",
    "circular_flow": "Large fraction of funds circulate back to origin",
}


def generate_explanations(
    G: nx.DiGraph, suspicious_accounts: dict, temporal_features: dict = None
) -> dict:
    """
    For each suspicious account, generate:
      - risk_breakdown: per-factor score details
      - detected_patterns: list of pattern labels
      - transaction_summary: basic stats
      - why_flagged: human-readable explanation string
    
    Returns dict: account_id -> explanation_dict
    """
    explanations = {}

    for account_id, data in suspicious_accounts.items():
        factor_scores = data.get("factor_scores", {})
        patterns = data.get("detected_patterns", [])
        score = data.get("suspicion_score", 0)

        # Build risk breakdown
        risk_breakdown = []
        for factor, fscore in sorted(factor_scores.items(), key=lambda x: -x[1]):
            if fscore > 0:
                desc = FACTOR_DESCRIPTIONS.get(factor, "")
                
                # Add dynamic details for time-based factors
                if factor == "velocity" and temporal_features:
                    tf = temporal_features.get(account_id, {})
                    vel = tf.get("velocity", 0)
                    burst = tf.get("burst_score", 0)

                    # Dynamic description based on what specifically triggered the score
                    if vel > 5.0 and burst > 5.0:
                        desc = f"High transaction frequency ({vel:.1f}/day) and burst activity (score {burst:.1f})"
                    elif vel > 5.0:
                        desc = f"Unusually high transaction frequency ({vel:.1f} txns/day)"
                    elif burst > 5.0:
                        desc = f"Sudden burst of activity relative to average behavior (burst score {burst:.1f})"
                    else:
                        desc = f"Velocity anomalies detected ({vel:.1f}/day, burst {burst:.1f})"
                
                risk_breakdown.append({
                    "factor": factor,
                    "score": fscore,
                    "description": desc,
                })

        # Transaction summary
        nd = G.nodes.get(account_id, {})
        txn_summary = {
            "total_sent": round(nd.get("total_sent", 0), 2),
            "total_received": round(nd.get("total_received", 0), 2),
            "total_volume": round(nd.get("total_volume", 0), 2),
            "transaction_count": nd.get("transaction_count", 0),
            "in_degree": nd.get("in_degree", 0),
            "out_degree": nd.get("out_degree", 0),
            "unique_counterparties": nd.get("unique_counterparties", 0),
        }

        # Build why_flagged narrative
        why_parts = []
        top_factors = [f for f in risk_breakdown if f["score"] >= 15]
        if not top_factors:
            top_factors = risk_breakdown[:2]

        for f in top_factors:
            why_parts.append(f["description"])

        ring_count = len(data.get("ring_ids", []))
        if ring_count > 1:
            why_parts.append(
                f"Appears in {ring_count} separate fraud rings, indicating central involvement"
            )

        why_flagged = (
            f"Account {account_id} received a risk score of {score}/100. "
            + ". ".join(why_parts) + "."
        )

        explanations[account_id] = {
            "risk_breakdown": risk_breakdown,
            "detected_patterns": patterns,
            "transaction_summary": txn_summary,
            "why_flagged": why_flagged,
            "suspicion_score": score,
            "ring_ids": data.get("ring_ids", []),
        }

    return explanations
