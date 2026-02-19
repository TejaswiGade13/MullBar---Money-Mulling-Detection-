import sys
import os
import pandas as pd

# Add current directory to path so imports work
sys.path.append(os.getcwd())

from engine.pipeline import analyze_pipeline

DATA_PATH = r"C:\Users\tejas\.gemini\antigravity\scratch\mullbar\adversarial_data.csv"

def verify():
    print(f"Loading data from {DATA_PATH}...")
    try:
        df = pd.read_csv(DATA_PATH)
        # Type enforcement
        df['transaction_id'] = df['transaction_id'].astype(str)
        df['sender_id'] = df['sender_id'].astype(str)
        df['receiver_id'] = df['receiver_id'].astype(str)
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    print("Running Pipeline...")
    try:
        results = analyze_pipeline(df)
    except Exception as e:
        print(f"Pipeline Failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    analysis = results['analysis']
    print(f"\nTotal Transactions: {analysis['summary']['total_transactions']}")
    print(f"High Risk Accounts: {analysis['summary']['high_risk_count']}")
    print(f"Fraud Rings Detected: {analysis['summary']['fraud_rings_count']}")
    
    print("\n--- Detection Detail ---")
    rings = analysis['fraud_rings']
    found_types = set(r['type'] for r in rings)
    print(f"Detected Ring Types: {found_types}")
    
    for ring in rings:
        print(f"- {ring['type']} (Length: {ring.get('length')})")
        
    # Check for Specific Expected Cases
    print("\n--- Verification Checks ---")
    scc_found = any(r['type'] == 'Cycle' for r in rings)
    layers_found = any(r['type'] == 'Layered Shell Network' for r in rings)
    
    print(f"Cycles Detected: {scc_found} (Expected: True)")
    print(f"Layered Shells Detected: {layers_found} (Expected: True)")
    
    if scc_found and layers_found:
        print("\n✅ CORE LOGIC PASSED")
    else:
        print("\n❌ LOGIC CHECK FAILED")

if __name__ == "__main__":
    verify()
