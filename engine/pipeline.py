"""
MullBar — Pipeline Orchestrator
Runs the full analysis pipeline in sequence.
"""

import time
import pandas as pd

from engine.ingestion import parse_csv
from engine.graph_builder import build_graph
from engine.detection import detect_cycles, detect_smurfing, detect_shell_networks
from engine.temporal import compute_temporal_features
from engine.behavioral import compute_behavioral_features
from engine.scoring import compute_composite_scores
from engine.rings import assign_ring_ids, aggregate_rings
from engine.explainability import generate_explanations
from engine.false_positives import filter_false_positives
from engine.output import generate_output
from engine.visualization import build_viz_data


def analyze_pipeline(df: pd.DataFrame) -> dict:
    """
    Full analysis pipeline.
    Returns {
        "results": <strict JSON output>,
        "graph": <Cytoscape.js viz data>,
        "explanations": <per-account explainability>,
    }
    """
    start_time = time.time()

    # 1. Build graph
    G = build_graph(df)

    # 2. Detection
    cycle_rings = detect_cycles(G)
    smurfing_rings = detect_smurfing(G, df)
    shell_rings = detect_shell_networks(G)
    all_rings = cycle_rings + smurfing_rings + shell_rings

    # 3. Assign ring IDs
    all_rings = assign_ring_ids(all_rings)

    # 4. Temporal analysis
    temporal_features = compute_temporal_features(G, df)

    # 5. Behavioral analysis
    behavioral_features = compute_behavioral_features(G)

    # 6. Composite risk scoring
    suspicious_accounts = compute_composite_scores(
        G, all_rings, temporal_features, behavioral_features
    )

    # 7. False positive filtering
    suspicious_accounts, removed_ring_ids = filter_false_positives(
        G, suspicious_accounts, df, all_rings
    )
    all_rings = [r for r in all_rings if r.get("ring_id", "") not in removed_ring_ids]

    # 8. Aggregate ring risk scores
    all_rings = aggregate_rings(G, suspicious_accounts, all_rings)

    # 9. Explainability
    explanations = generate_explanations(G, suspicious_accounts, temporal_features)

    # 10. Generate outputs
    processing_time = time.time() - start_time
    output_json = generate_output(
        suspicious_accounts, all_rings, G.number_of_nodes(), processing_time
    )
    graph_viz = build_viz_data(G, suspicious_accounts, all_rings, explanations)

    return {
        "results": output_json,
        "graph": graph_viz,
        "explanations": explanations,
    }
