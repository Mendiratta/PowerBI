# Growth Command Center — Flask version (exact HTML/CSS layout)

This version fixes the one thing the Dash build couldn't do: it uses your
**exact original HTML and CSS**, untouched — the same `dashboard.html`
markup and styling you already saw — and makes the filters real by having
the page call a small Python API whenever a dropdown changes.

## Why this looks identical (and Dash didn't)

Dash renders its own component markup (`dcc.Dropdown`, `dcc.Tabs`, etc.),
which comes with its own default CSS that fights a hand-built design system.
Flask does none of that — it just serves the HTML file as-is. The only
change from the static mockup: the big inline JSON blob is gone, and the
page now does `fetch('/api/data?...')` on load and on every filter change.

## 1. Folder structure

```
gcc_flask/
├── app.py             <- Flask app: two routes, "/" and "/api/data"
├── data_model.py       <- same pandas layer as the Dash version
├── requirements.txt
├── data/                <- same star-schema CSVs
└── templates/
    └── index.html        <- your original HTML/CSS, JS refactored to fetch data
```

## 2. Install & run

```bash
cd gcc_flask
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. Visually, this is pixel-for-pixel the same
dashboard you already reviewed. The difference: change the date range,
platform, or rep dropdown, and the whole page — KPI cards, every chart,
every table — recomputes from the real filtered data, because it's now
asking Python for fresh numbers instead of just re-reading a static blob.

## 3. How the filter flow works

1. Page loads → JS calls `refresh()` → `fetch('/api/data?date_range=Last 90 days&platform=All Platforms&rep=All Reps')`
2. Flask's `/api/data` route filters `fact_leads`/`fact_ad_spend` with pandas
   (`data_model.filter_data`), then builds the same JSON shape the static
   mockup used (`data_model.to_dashboard_json`)
3. The browser gets that JSON back and calls the same render functions
   (`renderExecKpis`, `renderCampaignTab`, etc.) that used to run once on
   page load — now they run on every filter change
4. Every chart is tracked in a `charts{}` object and destroyed/recreated on
   refresh, so Chart.js doesn't leak old instances or draw stale data

## 4. Where each dashboard section's logic lives

| Section | Python (data) | JS (render) |
|---|---|---|
| KPI cards | `compute_kpis()` | `renderExecKpis()` |
| Revenue vs spend / ROAS trend | `daily_trend()` | `renderExecCharts()` |
| Campaign table + chart | `campaign_table()` | `renderCampaignTab()` |
| Ad table + scatter | `ad_table()` | `renderAdTab()` |
| Platform donut/bar/table | `platform_table()` | `renderPlatformTab()` |
| Funnel | `funnel_counts()` | `renderFunnel()` |
| Sales team | `rep_table()` | `renderTeamTab()` |
| Trends (metric/granularity picker) | (client-side aggregation of `trend`) | `renderTrendTab()` |

## 5. Swapping in real data later

Same as before — `data_model.load_data()` is the only place reading CSVs.
Point it at a Meta Ads API pull and a Pipedrive export/API pull instead, and
nothing in `app.py` or `templates/index.html` needs to change.

## 6. Deploying this for the client to actually use every morning

Flask apps deploy the same way as any WSGI app:
```bash
pip install gunicorn
gunicorn app:app -b 0.0.0.0:8000
```
then put it behind Render, Railway, or a small VPS with nginx in front —
same idea as the Dash deployment note, just a slightly more standard/common
stack, which can be a talking point in your proposal since plain Flask apps
are cheaper to find hosting help for than Dash-specific deployments.
