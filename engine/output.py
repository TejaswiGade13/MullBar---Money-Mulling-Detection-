"""
MullBar — Output Generator
Produces the strict JSON output format.
"""


from collections import defaultdict

def generate_output(
    suspicious_accounts: dict,
    all_rings: list[dict],
    total_nodes: int,
    processing_time: float,
) -> list[dict]:
    """
    Generate a List of Grouped Entries (Cases).
    Each entry contains:
      - summary: stats for this specific group/ring
      - fraud_rings: list containing the specific ring definition
      - suspicious_accounts: list of detailed accounts in this ring
    """
    grouped_results = []
    
    # helper to format account
    def fmt_acc(acc_id, data, primary_ring):
        return {
            "account_id": acc_id,
            "suspicion_score": float(data["suspicion_score"]),
            "detected_patterns": data["detected_patterns"],
            "ring_id": primary_ring,
        }

    # Helper to format ring
    def fmt_ring(r):
        return {
            "ring_id": r.get("ring_id", "RING_000"),
            "member_accounts": r["members"],
            "pattern_type": r["pattern_type"],
            "risk_score": float(r.get("risk_score", 0)),
        }

    # 1. Map ring_id -> [Accounts]
    accounts_by_ring = defaultdict(list)
    isolated_accounts = []

    for acc_id, data in sorted(
        suspicious_accounts.items(),
        key=lambda x: x[1]["suspicion_score"],
        reverse=True,
    ):
        r_ids = data.get("ring_ids", [])
        if r_ids:
            # Add to primary ring (first one)
            # We could add to all, but primary avoids duplication if user just wants simple list
            primary = r_ids[0]
            accounts_by_ring[primary].append(fmt_acc(acc_id, data, primary))
        else:
            isolated_accounts.append(fmt_acc(acc_id, data, "RING_000"))

    # 2. Build entries for each detected Ring
    # Sort rings by risk score descending
    sorted_rings = sorted(all_rings, key=lambda x: x.get("risk_score", 0), reverse=True)

    for ring in sorted_rings:
        rid = ring.get("ring_id")
        members = accounts_by_ring.get(rid, [])
        
        entry = {
            "summary": {
                "group_type": "fraud_ring",
                "description": f"Detected {ring['pattern_type']} pattern",
                "account_count": int(len(members)),
                "risk_score": float(ring.get("risk_score", 0)),
            },
            "fraud_rings": [fmt_ring(ring)],
            "suspicious_accounts": members
        }
        grouped_results.append(entry)

    # 3. Entry for Isolated Suspicious Accounts (if any)
    if isolated_accounts:
        grouped_results.append({
            "summary": {
                "group_type": "isolated_suspicious",
                "description": "Suspicious accounts not linked to any ring",
                "account_count": int(len(isolated_accounts)),
                "risk_score": 0.0
            },
            "fraud_rings": [],
            "suspicious_accounts": isolated_accounts
        })
    
    # 4. If no detections at all, return empty structure with global summary
    if not grouped_results:
         grouped_results.append({
            "summary": {
                "group_type": "analysis_stats",
                "description": "No fraud patterns detected",
                "total_analyzed": int(total_nodes),
                "processing_time": round(float(processing_time), 2)
            },
            "fraud_rings": [],
            "suspicious_accounts": []
         })

    return grouped_results