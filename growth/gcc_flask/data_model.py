"""
data_model.py
--------------
Loads the star-schema CSVs and exposes filter + aggregation functions.
This plays the same role pandas-side that your DAX measures play in Power BI:
  - load_data()      -> the equivalent of Power Query importing + relating tables
  - filter_data()     -> the equivalent of your Date/Platform/Rep slicers narrowing context
  - compute_kpis()    -> the equivalent of Total Revenue / ROAS / CPL / etc. measures
"""

import pandas as pd
from datetime import timedelta

DATA_DIR = "data"


def load_data():
    """Load and join the star schema into two flat, analysis-ready frames."""
    dim_date = pd.read_csv(f"{DATA_DIR}/dim_date.csv", parse_dates=["date"])
    dim_campaign = pd.read_csv(f"{DATA_DIR}/dim_campaign.csv")
    dim_ad = pd.read_csv(f"{DATA_DIR}/dim_ad.csv")
    dim_rep = pd.read_csv(f"{DATA_DIR}/dim_salesrep.csv")

    leads = pd.read_csv(f"{DATA_DIR}/fact_leads.csv", parse_dates=["date"]).drop(columns=["platform"])
    spend = pd.read_csv(f"{DATA_DIR}/fact_ad_spend.csv", parse_dates=["date"]).drop(columns=["platform"])

    # This merge step is the pandas equivalent of the relationships you built
    # in Power BI's Model view (dim tables -> fact tables on their key columns).
    leads = leads.merge(dim_campaign, on="campaign_id", how="left") \
                 .merge(dim_ad[["ad_id", "ad_name"]], on="ad_id", how="left") \
                 .merge(dim_rep, on="rep_id", how="left")

    spend = spend.merge(dim_campaign, on="campaign_id", how="left") \
                 .merge(dim_ad[["ad_id", "ad_name"]], on="ad_id", how="left")

    return leads, spend, dim_date


def get_date_bounds(dim_date, date_range_label):
    """Equivalent of your Selected Start Date / Selected End Date measures."""
    max_date = dim_date["date"].max()
    if date_range_label == "Last 7 days":
        start = max_date - timedelta(days=6)
    elif date_range_label == "Last 30 days":
        start = max_date - timedelta(days=29)
    elif date_range_label == "Last 90 days":
        start = max_date - timedelta(days=89)
    elif date_range_label == "Month to Date":
        start = max_date.replace(day=1)
    elif date_range_label == "Year to Date":
        start = max_date.replace(month=1, day=1)
    else:
        start = max_date - timedelta(days=89)
    return start, max_date


def filter_data(leads, spend, dim_date, date_range_label, platform, rep):
    """
    Equivalent of KEEPFILTERS(DATESBETWEEN(...)) + the platform/rep FILTER(ALL(...))
    pattern from the Power BI measures -- but here it's just a boolean mask,
    so there's no context-collision risk the way there is in DAX.
    """
    start, end = get_date_bounds(dim_date, date_range_label)

    l = leads[(leads["date"] >= start) & (leads["date"] <= end)]
    s = spend[(spend["date"] >= start) & (spend["date"] <= end)]

    if platform and platform != "All Platforms":
        l = l[l["platform"] == platform]
        s = s[s["platform"] == platform]
    if rep and rep != "All Reps":
        l = l[l["rep_name"] == rep]

    return l, s, start, end


def compute_kpis(l, s):
    """Equivalent of the Total Revenue / ROAS / CPL / etc. DAX measures."""
    spend_total = s["spend"].sum()
    leads_total = len(l)
    calls_booked = l["call_booked"].sum()
    calls_completed = l["call_completed"].sum()
    sales_total = l["sale_won"].sum()
    revenue_total = l["sale_value"].sum()

    return {
        "revenue": revenue_total,
        "spend": spend_total,
        "leads": leads_total,
        "calls_booked": int(calls_booked),
        "calls_completed": int(calls_completed),
        "show_rate": (calls_completed / calls_booked * 100) if calls_booked else 0,
        "sales": int(sales_total),
        "avg_sale_value": (revenue_total / sales_total) if sales_total else 0,
        "roas": (revenue_total / spend_total) if spend_total else 0,
        "cost_per_lead": (spend_total / leads_total) if leads_total else 0,
        "cost_per_sale": (spend_total / sales_total) if sales_total else 0,
        "close_rate": (sales_total / calls_completed * 100) if calls_completed else 0,
    }


def compute_prior_period_kpis(leads, spend, dim_date, date_range_label, platform, rep):
    """Equivalent of the *_PP measures — same window length, shifted immediately before."""
    start, end = get_date_bounds(dim_date, date_range_label)
    n_days = (end - start).days + 1
    pp_start = start - timedelta(days=n_days)
    pp_end = start - timedelta(days=1)

    l = leads[(leads["date"] >= pp_start) & (leads["date"] <= pp_end)]
    s = spend[(spend["date"] >= pp_start) & (spend["date"] <= pp_end)]
    if platform and platform != "All Platforms":
        l = l[l["platform"] == platform]
        s = s[s["platform"] == platform]
    if rep and rep != "All Reps":
        l = l[l["rep_name"] == rep]

    return compute_kpis(l, s)


def daily_trend(l, s):
    """Equivalent of the date-table-driven trend chart. Schema matches the
    original static HTML mockup's `trend` array exactly, so the same
    front-end JS can consume it unmodified."""
    rev = l.groupby(l["date"].dt.date)["sale_value"].sum().rename("revenue")
    leads_ct = l.groupby(l["date"].dt.date).size().rename("leads")
    booked = l.groupby(l["date"].dt.date)["call_booked"].sum().rename("calls_booked")
    completed = l.groupby(l["date"].dt.date)["call_completed"].sum().rename("calls_completed")
    sales_ct = l.groupby(l["date"].dt.date)["sale_won"].sum().rename("sales")
    sp = s.groupby(s["date"].dt.date)["spend"].sum().rename("spend")
    df = pd.concat([rev, leads_ct, booked, completed, sales_ct, sp], axis=1).fillna(0).reset_index()
    df.columns = ["date", "revenue", "leads", "calls_booked", "calls_completed", "sales", "spend"]
    df["roas"] = (df["revenue"] / df["spend"]).replace([float("inf")], 0).fillna(0).round(2)
    df["date"] = df["date"].astype(str)
    return df.sort_values("date")


def to_dashboard_json(l, s):
    """
    Assemble the exact JSON shape the original standalone HTML dashboard
    expects (exec_summary / trend / campaign_table / ad_table /
    platform_table / funnel / rep_table), from filtered leads/spend frames.
    Using df.to_json()->json.loads() (rather than df.to_dict()) so numpy
    int64/float64 types are converted to plain JSON-safe Python types.
    """
    import json as _json

    kpis = compute_kpis(l, s)
    trend_df = daily_trend(l, s)
    camp_df = campaign_table(l, s)
    ad_df = ad_table(l, s)
    plat_df = platform_table(l, s)
    rep_df = rep_table(l)
    funnel = funnel_counts(l)

    return {
        "exec_summary": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in kpis.items()},
        "trend": _json.loads(trend_df.to_json(orient="records")),
        "campaign_table": _json.loads(camp_df.round(2).to_json(orient="records")),
        "ad_table": _json.loads(ad_df.round(2).to_json(orient="records")),
        "platform_table": _json.loads(plat_df.round(2).to_json(orient="records")),
        "funnel": funnel,
        "rep_table": _json.loads(rep_df.round(2).to_json(orient="records")),
    }


def campaign_table(l, s):
    spend_by_camp = s.groupby(["campaign_id", "campaign_name", "platform"])["spend"].sum()
    agg = l.groupby(["campaign_id", "campaign_name", "platform"]).agg(
        leads=("lead_id", "count"),
        calls_booked=("call_booked", "sum"),
        calls_completed=("call_completed", "sum"),
        sales=("sale_won", "sum"),
        revenue=("sale_value", "sum"),
    )
    df = agg.join(spend_by_camp, how="left").reset_index().fillna(0)
    df["cost_per_lead"] = (df["spend"] / df["leads"]).replace([float("inf")], 0).fillna(0)
    df["cost_per_sale"] = (df["spend"] / df["sales"]).replace([float("inf")], 0).fillna(0)
    df["show_rate"] = (df["calls_completed"] / df["calls_booked"] * 100).replace([float("inf")], 0).fillna(0)
    df["roas"] = (df["revenue"] / df["spend"]).replace([float("inf")], 0).fillna(0)
    df["conversion_rate"] = (df["sales"] / df["leads"] * 100).replace([float("inf")], 0).fillna(0)
    return df.sort_values("revenue", ascending=False)


def ad_table(l, s):
    spend_by_ad = s.groupby(["ad_id", "ad_name", "campaign_id"])["spend"].sum()
    agg = l.groupby(["ad_id", "ad_name", "campaign_id"]).agg(
        leads=("lead_id", "count"),
        sales=("sale_won", "sum"),
        revenue=("sale_value", "sum"),
    )
    df = agg.join(spend_by_ad, how="left").reset_index().fillna(0)
    df["cost_per_lead"] = (df["spend"] / df["leads"]).replace([float("inf")], 0).fillna(0)
    df["roas"] = (df["revenue"] / df["spend"]).replace([float("inf")], 0).fillna(0)
    df["conversion_rate"] = (df["sales"] / df["leads"] * 100).replace([float("inf")], 0).fillna(0)
    return df.sort_values("roas", ascending=False)


def platform_table(l, s):
    spend_by_plat = s.groupby("platform")["spend"].sum()
    agg = l.groupby("platform").agg(
        leads=("lead_id", "count"),
        sales=("sale_won", "sum"),
        revenue=("sale_value", "sum"),
    )
    df = agg.join(spend_by_plat, how="left").reset_index().fillna(0)
    df["cost_per_lead"] = (df["spend"] / df["leads"]).replace([float("inf")], 0).fillna(0)
    df["roas"] = (df["revenue"] / df["spend"]).replace([float("inf")], 0).fillna(0)
    return df.sort_values("revenue", ascending=False)


def rep_table(l):
    r = l[l["rep_name"].notna()]
    agg = r.groupby("rep_name").agg(
        calls_completed=("call_completed", "sum"),
        sales=("sale_won", "sum"),
        revenue=("sale_value", "sum"),
    ).reset_index()
    agg["close_rate"] = (agg["sales"] / agg["calls_completed"] * 100).replace([float("inf")], 0).fillna(0)
    agg["avg_sale_value"] = (agg["revenue"] / agg["sales"]).replace([float("inf")], 0).fillna(0)
    return agg.sort_values("revenue", ascending=False)


def funnel_counts(l):
    return {
        "leads": len(l),
        "calls_booked": int(l["call_booked"].sum()),
        "calls_completed": int(l["call_completed"].sum()),
        "sales": int(l["sale_won"].sum()),
    }
