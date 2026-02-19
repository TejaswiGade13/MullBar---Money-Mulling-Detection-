"""
MullBar — Data Ingestion Layer
Handles CSV parsing, validation, and type coercion.
"""

import io
import pandas as pd


REQUIRED_COLUMNS = ["transaction_id", "sender_id", "receiver_id", "amount", "timestamp"]


def parse_csv(file_content: bytes) -> pd.DataFrame:
    """
    Parse CSV file content into a validated DataFrame.
    Raises ValueError with descriptive messages on invalid input.
    """
    try:
        text = file_content.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("File encoding must be UTF-8.")

    if not text.strip():
        raise ValueError("Uploaded file is empty.")

    df = pd.read_csv(io.StringIO(text))

    # --- Column validation ---
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}. "
            f"Expected columns: {', '.join(REQUIRED_COLUMNS)}"
        )

    extra = [c for c in df.columns if c not in REQUIRED_COLUMNS]
    # Extra columns are silently dropped
    df = df[REQUIRED_COLUMNS].copy()

    # --- Type coercion ---
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if df["amount"].isna().any():
        bad_count = df["amount"].isna().sum()
        raise ValueError(f"{bad_count} rows have non-numeric 'amount' values.")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if df["timestamp"].isna().any():
        bad_count = df["timestamp"].isna().sum()
        raise ValueError(
            f"{bad_count} rows have invalid 'timestamp' values. "
            "Expected format: YYYY-MM-DD HH:MM:SS"
        )

    # --- String columns ---
    for col in ["transaction_id", "sender_id", "receiver_id"]:
        df[col] = df[col].astype(str).str.strip()
        if (df[col] == "").any() or df[col].isna().any():
            raise ValueError(f"Column '{col}' contains empty values.")

    # --- Dedup check ---
    if df["transaction_id"].duplicated().any():
        dup_count = df["transaction_id"].duplicated().sum()
        raise ValueError(f"{dup_count} duplicate transaction_id values found.")

    # Sort by timestamp for temporal analysis
    df = df.sort_values("timestamp").reset_index(drop=True)

    return df
