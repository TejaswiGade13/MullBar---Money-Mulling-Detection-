"""
Generate a 10,000-row test CSV with realistic transaction data
and embedded fraud patterns (cycles, smurfing, shell networks).
"""
import csv
import random
import uuid
from datetime import datetime, timedelta

random.seed(42)

NUM_TRANSACTIONS = 10000
NUM_NORMAL_ACCOUNTS = 300
NUM_MULE_ACCOUNTS = 40
NUM_SHELL_ACCOUNTS = 15

# Generate account IDs
normal_accounts = [f"ACC_{i:04d}" for i in range(1, NUM_NORMAL_ACCOUNTS + 1)]
mule_accounts = [f"MULE_{i:03d}" for i in range(1, NUM_MULE_ACCOUNTS + 1)]
shell_accounts = [f"SHELL_{i:03d}" for i in range(1, NUM_SHELL_ACCOUNTS + 1)]
all_accounts = normal_accounts + mule_accounts + shell_accounts

start_date = datetime(2025, 1, 1)
rows = []

def rand_ts():
    return start_date + timedelta(
        days=random.randint(0, 90),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )

def add_txn(sender, receiver, amount, ts=None):
    rows.append({
        "transaction_id": f"TXN_{uuid.uuid4().hex[:12].upper()}",
        "sender_id": sender,
        "receiver_id": receiver,
        "amount": round(amount, 2),
        "timestamp": (ts or rand_ts()).strftime("%Y-%m-%d %H:%M:%S"),
    })

# ─── 1. Normal transactions (~7000) ───
for _ in range(7000):
    s = random.choice(normal_accounts)
    r = random.choice(normal_accounts)
    while r == s:
        r = random.choice(normal_accounts)
    add_txn(s, r, random.uniform(10, 5000))

# ─── 2. Cycle patterns (A→B→C→A, repeated) ───
for cycle_id in range(8):
    members = random.sample(mule_accounts, random.choice([3, 4, 5]))
    base_ts = rand_ts()
    for repeat in range(random.randint(5, 15)):
        for i in range(len(members)):
            src = members[i]
            dst = members[(i + 1) % len(members)]
            ts = base_ts + timedelta(hours=repeat * 2 + i)
            add_txn(src, dst, random.uniform(500, 3000), ts)

# ─── 3. Fan-in smurfing (many → 1 aggregator) ───
for _ in range(3):
    aggregator = random.choice(mule_accounts)
    senders = random.sample(normal_accounts, random.randint(12, 20))
    base_ts = rand_ts()
    for i, sender in enumerate(senders):
        for rep in range(random.randint(3, 8)):
            ts = base_ts + timedelta(hours=i + rep * 6)
            add_txn(sender, aggregator, random.uniform(100, 900), ts)

# ─── 4. Fan-out smurfing (1 disperser → many) ───
for _ in range(3):
    disperser = random.choice(mule_accounts)
    receivers = random.sample(normal_accounts, random.randint(12, 18))
    base_ts = rand_ts()
    for i, receiver in enumerate(receivers):
        for rep in range(random.randint(3, 6)):
            ts = base_ts + timedelta(hours=i + rep * 4)
            add_txn(disperser, receiver, random.uniform(200, 800), ts)

# ─── 5. Shell network chains (origin → shell → shell → ... → destination) ───
for _ in range(5):
    chain_len = random.randint(3, 5)
    chain = random.sample(shell_accounts, min(chain_len, len(shell_accounts)))
    origin = random.choice(mule_accounts)
    dest = random.choice(normal_accounts)
    full_chain = [origin] + chain + [dest]
    base_ts = rand_ts()
    for rep in range(random.randint(3, 8)):
        for i in range(len(full_chain) - 1):
            ts = base_ts + timedelta(hours=rep * 12 + i * 2)
            add_txn(full_chain[i], full_chain[i + 1], random.uniform(1000, 5000), ts)

# ─── 6. Fill remaining to reach 10k ───
while len(rows) < NUM_TRANSACTIONS:
    s = random.choice(all_accounts)
    r = random.choice(all_accounts)
    while r == s:
        r = random.choice(all_accounts)
    add_txn(s, r, random.uniform(50, 3000))

# Shuffle and trim
random.shuffle(rows)
rows = rows[:NUM_TRANSACTIONS]

# Write CSV
output = "test_10k.csv"
with open(output, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["transaction_id", "sender_id", "receiver_id", "amount", "timestamp"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} transactions → {output}")
print(f"  Normal accounts: {NUM_NORMAL_ACCOUNTS}")
print(f"  Mule accounts:   {NUM_MULE_ACCOUNTS}")
print(f"  Shell accounts:  {NUM_SHELL_ACCOUNTS}")
print(f"  Embedded patterns: 8 cycles, 3 fan-in, 3 fan-out, 5 shell chains")
