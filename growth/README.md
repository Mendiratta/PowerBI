# Growth Command Center

**A morning-open KPI dashboard for marketing & sales — built with Python, Flask, and pandas.**

One dashboard. Every morning. The full health of the business — revenue, marketing spend, leads, calls, sales, and ROAS, sliced by date range, platform, and sales rep.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.x-150458?logo=pandas&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What this is

A KPI dashboard for businesses running paid marketing (Meta, Google, TikTok, etc.) with a sales team following up on leads. It answers, in under five minutes:

- Is revenue up or down vs. the prior period, and why?
- Which campaigns and ads are actually profitable — and which are burning budget?
- Where is the funnel leaking — lead → call booked → call completed → sale?
- Which sales rep is converting best?

Built to be **scalable by design** — a proper star-schema data model underneath, so adding a new marketing platform or a new sales rep is a data change, not a rebuild.

---

## Screenshots

> ![Executive Overview](docs/screenshots/executive.png)
> ![Campaign Performance](docs/screenshots/campaign.png)
> ![Ad / Creative Performance](docs/screenshots/creative.png)
> ![Platform Comparision](docs/screenshots/platform.png)
> ![Sales Funnel](docs/screenshots/sales.png)
> ![Sales Team](docs/screenshots/teams.png)
> ![Trends](docs/screenshots/trend.png)
> ```

---

## Tech stack

| Layer | Tool | Why |
|---|---|---|
| Data model | **pandas** | star-schema joins + aggregation, the same relationships you'd build in Power BI |
| Backend | **Flask** | serves the dashboard page + a small `/api/data` endpoint that recomputes KPIs per filter selection |
| Frontend | **HTML / CSS / vanilla JS + Chart.js** | no frontend framework — kept deliberately simple and fast |
| Data source (current) | **Synthetic CSVs** (`/data`) | star schema: `dim_date`, `dim_campaign`, `dim_ad`, `dim_salesrep` + `fact_leads`, `fact_ad_spend` |
| Data source (planned) | **Meta Ads API + Pipedrive API** | see [Roadmap](#roadmap) |

---

## Project structure

```
gcc_flask/
├── app.py                 # Flask app: "/" page route + "/api/data" JSON endpoint
├── data_model.py            # pandas layer — filtering + KPI/aggregation logic
├── requirements.txt
├── data/                     # star-schema CSVs (synthetic sample data)
│   ├── dim_date.csv
│   ├── dim_campaign.csv
│   ├── dim_ad.csv
│   ├── dim_salesrep.csv
│   ├── fact_leads.csv
│   └── fact_ad_spend.csv
├── static/
│   ├── logo.png
│   ├── favicon.ico
│   └── ...                    # favicon set (see below)
└── templates/
    └── index.html              # the dashboard UI (Jinja2 template)
```

---

## Getting started

### 1. Clone and install

```bash
git clone https://github.com/<your-username>/growth-command-center.git
cd growth-command-center
pip install -r requirements.txt
```

### 2. Run

```bash
python app.py
```

Open **http://127.0.0.1:5000** — filters (date range, platform, sales rep) call `/api/data` and re-render the whole page live.

---

## Data model

A star schema — the same shape you'd build in Power BI or any BI tool:

```
dim_date ──┐
dim_campaign ──┤
dim_ad ────────┼──< fact_leads
dim_salesrep ──┘
                
dim_campaign ──┐
dim_ad ────────┼──< fact_ad_spend
dim_date ──────┘
```

- **`fact_leads`** — one row per lead: source ad/campaign, call booked/completed flags, sale won flag + value, assigned rep
- **`fact_ad_spend`** — one row per ad, per day: spend
- Dimension tables are small and mostly static — this is where a real Meta/Pipedrive integration would write incremental data on a schedule

Core measures (in `data_model.py`, equivalent to DAX measures in Power BI):

```python
Total Revenue   = sum(fact_leads.sale_value)
ROAS            = Total Revenue / Total Spend
Cost Per Lead   = Total Spend / Total Leads
Cost Per Sale   = Total Spend / Total Sales
Show Rate       = Calls Completed / Calls Booked
Conversion Rate = Sales / Leads
```

---

## Dashboard sections

| Tab | What it shows |
|---|---|
| **Executive Overview** | 12 KPI cards, revenue-vs-spend trend, ROAS trend, top campaigns |
| **Campaign Performance** | Full sortable table + spend-vs-revenue chart, per campaign |
| **Ad / Creative Performance** | Winner/Watch/Losing tags by ROAS, CPL-vs-ROAS scatter plot |
| **Platform Comparison** | Revenue share + ROAS, across Facebook/Instagram/Google/TikTok/Organic/Referral/Email |
| **Sales Funnel** | Lead → call booked → call completed → sale, with stage conversion % |
| **Sales Team** | Revenue, close rate, and average sale value by rep |
| **Trends** | Daily / weekly / monthly view of any core metric |

---

## Roadmap

- [ ] Replace synthetic `fact_ad_spend.csv` with a scheduled **Meta Marketing API** pull
- [ ] Replace synthetic `fact_leads.csv` with a scheduled **Pipedrive API** pull
- [ ] Add Google Ads and TikTok Ads as additional platform sources
- [ ] Add a country/geography filter
- [ ] Scheduled daily refresh (cron / task scheduler) instead of on-demand recompute
- [ ] Optional auth layer if this ever needs to be exposed beyond localhost

---

## License

MIT — 
---

## Author

Built by **Vikram Mendiratta** — FP&A and BI consultant, Power BI / Python / SQL.
📧 Open an issue or reach out via [Upwork](#) / [LinkedIn](#) for consulting inquiries.