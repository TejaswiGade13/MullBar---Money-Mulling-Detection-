"""
MullBar — Flask Backend
Serves the analysis API and static frontend files.
Direct port of the FastAPI backend.
"""

import io
import os
import traceback

from flask import Flask, request, jsonify, render_template, send_from_directory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from engine.ingestion import parse_csv
from engine.pipeline import analyze_pipeline

app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return "OK", 200


@app.route("/api/analyze", methods=["POST"])
def analyze_csv():
    """Accept CSV file upload, run full analysis pipeline, return results."""
    if "file" not in request.files:
        return jsonify({"status": "error", "detail": "No file uploaded."}), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({"status": "error", "detail": "No file selected."}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"status": "error", "detail": "File must be a CSV."}), 400

    try:
        content = file.read()
        df = parse_csv(content)
    except ValueError as e:
        return jsonify({"status": "error", "detail": str(e)}), 400

    if df.empty:
        return jsonify({"status": "error", "detail": "No valid transactions found in CSV."}), 400

    try:
        result = analyze_pipeline(df)
        return jsonify({"status": "success", **result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "detail": f"Analysis failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
