"""
app.py — Growth Command Center (Flask version)

Serves the EXACT same HTML/CSS as the original static mockup. The only
difference from the static version: instead of one JSON blob baked into the
page at build time, the page calls /api/data whenever a filter changes, and
Python (pandas) recomputes the numbers for that exact selection.

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, jsonify
import data_model as dm

app = Flask(__name__)

# Load once at startup — cheap enough for this data size, and avoids
# re-reading CSVs from disk on every request.
leads_all, spend_all, dim_date = dm.load_data()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    date_range = request.args.get("date_range", "Last 90 days")
    platform = request.args.get("platform", "All Platforms")
    rep = request.args.get("rep", "All Reps")

    l, s, start, end = dm.filter_data(leads_all, spend_all, dim_date, date_range, platform, rep)
    payload = dm.to_dashboard_json(l, s)
    payload["meta"] = {
        "date_range": date_range, "platform": platform, "rep": rep,
        "start": str(start.date()), "end": str(end.date()),
    }
    return jsonify(payload)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
