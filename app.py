"""
MullBar — Flask Backend
Serves the analysis API and static frontend files.
Direct port of the FastAPI backend.
"""

import io
import os
import traceback

from flask import Flask, request, jsonify, send_from_directory

# Deferred imports for faster startup
# from engine.ingestion import parse_csv
# from engine.pipeline import analyze

app = Flask(__name__, static_folder="static", template_folder="templates")
app.json.sort_keys = False
app.config["JSON_SORT_KEYS"] = False


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


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
        from engine.ingestion import parse_csv
        from engine.pipeline import analyze
        
        content = file.read()
        df = parse_csv(content)
    except ValueError as e:
        return jsonify({"status": "error", "detail": str(e)}), 400

    if df.empty:
        return jsonify({"status": "error", "detail": "No valid transactions found in CSV."}), 400

    try:
        result = analyze(df)
        return jsonify({"status": "success", **result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "detail": f"Analysis failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
