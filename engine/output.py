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
) -> dict:
    """
    Generate output in the User-Requested Account-Centric Format.
    
    Structure:
    {
      "results": [
        {
          "suspicious_account": { ... },
          "fraud_ring": { ... }
        }
      ],
      "summary": { ... }
    }
    """
    results_list = []

    # Map ring_id -> ring_data for fast lookup
    rings_map = {r.get("ring_id", "RING_000"): r for r in all_rings}

    # Iterate through all suspicious accounts
    for acc_id, data in sorted(
        suspicious_accounts.items(),
        key=lambda x: x[1]["suspicion_score"],
        reverse=True,
    ):
        # 1. Format Account Data
        # Use first ring as primary if available
        primary_ring_id = data["ring_ids"][0] if data.get("ring_ids") else "RING_000"
        
        account_obj = {
            "account_id": acc_id,
            "suspicion_score": float(data["suspicion_score"]),
            "detected_patterns": data["detected_patterns"],
            "ring_id": primary_ring_id
        }

        # 2. Format Associated Ring Data
        ring_data = rings_map.get(primary_ring_id)
        
        if ring_data:
            ring_obj = {
                "ring_id": ring_data.get("ring_id", "RING_000"),
                "member_accounts": ring_data["members"],
                "pattern_type": ring_data["pattern_type"],
                "risk_score": float(ring_data.get("risk_score", 0))
            }
        else:
            # Fallback if no ring found (or RING_000)
            ring_obj = {
                "ring_id": "N/A",
                "member_accounts": [],
                "pattern_type": "none",
                "risk_score": 0.0
            }

        # 3. Create Entry
        results_list.append({
            "suspicious_account": account_obj,
            "fraud_ring": ring_obj
        })

    # Global Summary
    summary_obj = {
        "total_accounts_analyzed": int(total_nodes),
        "suspicious_accounts_flagged": int(len(results_list)),
        "fraud_rings_detected": int(len(all_rings)),
        "processing_time_seconds": round(float(processing_time), 2)
    }

    return {
        "results": results_list,
        "summary": summary_obj
    }