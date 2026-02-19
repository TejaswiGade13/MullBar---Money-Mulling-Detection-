"""
MullBar — Output Generator
Produces the strict JSON output format.
"""


'''def generate_output(
    suspicious_accounts: dict,
    all_rings: list[dict],
    total_nodes: int,
    processing_time: float,
) -> dict:
    """
    Generate the exact JSON output schema:
    {
      "suspicious_accounts": [...],
      "fraud_rings": [...],
      "summary": {...}
    }
    """
    # Build suspicious_accounts array (sorted by score desc)
    suspicious_list = []
    for account_id, data in sorted(
        suspicious_accounts.items(),
        key=lambda x: x[1]["suspicion_score"],
        reverse=True,
    ):
        primary_ring = data["ring_ids"][0] if data.get("ring_ids") else "RING_000"
        suspicious_list.append({
            "account_id": account_id,
            "suspicion_score": data["suspicion_score"],
            "detected_patterns": data["detected_patterns"],
            "ring_id": primary_ring,
        })

    # Build fraud_rings array
    fraud_rings_list = []
    for ring in all_rings:
        ring_id = ring.get("ring_id", "RING_000")
        risk_score = ring.get("risk_score", 0)
        fraud_rings_list.append({
            "ring_id": ring_id,
            "member_accounts": ring["members"],
            "pattern_type": ring["pattern_type"],
            "risk_score": risk_score,
        })

    output = {
        "suspicious_accounts": suspicious_list,
        "fraud_rings": fraud_rings_list,
        "summary": {
            "total_accounts_analyzed": int(total_nodes),
            "suspicious_accounts_flagged": int(len(suspicious_list)),
            "fraud_rings_detected": int(len(fraud_rings_list)),
            "processing_time_seconds": round(float(processing_time), 2),
        },
    }

    return output'''
'''def generate_output(
    suspicious_accounts: dict,
    all_rings: list[dict],
    total_nodes: int,
    processing_time: float,
) -> dict:
    """
    Generate strict JSON output schema matching required format.
    """

    # Build suspicious_accounts array (sorted by suspicion_score desc)
    suspicious_list = []
    for account_id, data in sorted(
        suspicious_accounts.items(),
        key=lambda x: float(x[1].get("suspicion_score", 0)),
        reverse=True,
    ):
        suspicious_list.append({
            "account_id": str(account_id),
            "suspicion_score": float(data.get("suspicion_score", 0)),
            "detected_patterns": list(data.get("detected_patterns", [])),
            "ring_id": (
                data.get("ring_ids")[0]
                if data.get("ring_ids")
                else None
            ),
        })

    # Build fraud_rings array
    fraud_rings_list = []
    for ring in all_rings:
        fraud_rings_list.append({
            "ring_id": ring.get("ring_id"),
            "member_accounts": list(ring.get("members", [])),
            "pattern_type": ring.get("pattern_type"),
            "risk_score": float(ring.get("risk_score", 0)),
        })

    # Final output
    output = {
        "suspicious_accounts": suspicious_list,
        "fraud_rings": fraud_rings_list,
        "summary": {
            "total_accounts_analyzed": int(total_nodes),
            "suspicious_accounts_flagged": int(len(suspicious_list)),
            "fraud_rings_detected": int(len(fraud_rings_list)),
            "processing_time_seconds": float(round(processing_time, 2)),
        },
    }

    return output'''
def generate_output(
    suspicious_accounts: dict,
    all_rings: list,
    total_nodes: int,
    processing_time: float,
) -> dict:

    # Create lookup for rings by id
    ring_lookup = {ring.get("ring_id"): ring for ring in all_rings}

    results = []

    for account_id, data in sorted(
        suspicious_accounts.items(),
        key=lambda x: x[1].get("suspicion_score", 0),
        reverse=True,
    ):

        ring_ids = data.get("ring_ids") or []
        ring_id = ring_ids[0] if ring_ids else None

        suspicious_obj = {
            "account_id": str(account_id),
            "suspicion_score": float(data.get("suspicion_score", 0)),
            "detected_patterns": list(data.get("detected_patterns", [])),
            "ring_id": ring_id,
        }

        ring_data = ring_lookup.get(ring_id, {})

        fraud_ring_obj = {
            "ring_id": ring_id,
            "member_accounts": list(ring_data.get("members", [])),
            "pattern_type": ring_data.get("pattern_type"),
            "risk_score": float(ring_data.get("risk_score", 0)),
        }

        results.append({
            "suspicious_account": suspicious_obj,
            "fraud_ring": fraud_ring_obj,
        })

    output = {
        "results": results,
        "summary": {
            "total_accounts_analyzed": int(total_nodes),
            "suspicious_accounts_flagged": len(results),
            "fraud_rings_detected": len(all_rings),
            "processing_time_seconds": round(float(processing_time), 2),
        },
    }

    return output

