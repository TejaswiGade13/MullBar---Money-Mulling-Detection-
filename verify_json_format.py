
import json
from engine.output import generate_output

# Mock data
suspicious_accounts = {
    "ACC_00123": {
        "suspicion_score": 87.5,
        "detected_patterns": ["cycle_length_3", "high_velocity"],
        "ring_ids": ["RING_001"]
    },
    "ACC_00456": {
        "suspicion_score": 45.0,
        "detected_patterns": ["fan_in_smurfing"],
        "ring_ids": ["RING_002"]
    }
}

all_rings = [
    {
        "ring_id": "RING_001",
        "members": ["ACC_00123", "ACC_00789", "ACC_00123"],
        "pattern_type": "cycle",
        "risk_score": 95.3,
        "pattern_label": "cycle_length_3"
    },
    {
        "ring_id": "RING_002",
        "members": ["ACC_00456", "ACC_00999"],
        "pattern_type": "fan_in",
        "risk_score": 50.0,
        "pattern_label": "fan_in_smurfing"
    }
]

output = generate_output(suspicious_accounts, all_rings, 500, 2.3456)
print(json.dumps(output, indent=2))
