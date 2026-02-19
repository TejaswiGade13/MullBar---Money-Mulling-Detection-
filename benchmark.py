"""Quick performance benchmark for 10K CSV."""
import time
from engine.ingestion import parse_csv
from engine.pipeline import analyze

data = open("test_10k.csv", "rb").read()
df = parse_csv(data)

print(f"Loaded {len(df)} transactions")
t = time.time()
result = analyze(df)
elapsed = time.time() - t

s = result["results"]["summary"]
print(f"Total time: {elapsed:.2f}s")
print(f"Accounts analyzed: {s['total_accounts_analyzed']}")
print(f"Suspicious flagged: {s['suspicious_accounts_flagged']}")
print(f"Fraud rings: {s['fraud_rings_detected']}")
print(f"Pipeline reports: {s['processing_time_seconds']:.2f}s")
