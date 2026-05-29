"""
utils/charts.py - Comprehensive Plotly chart builders (upgraded)
"""
from __future__ import annotations
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from config import CHART_COLORS, MONTH_NUM_TO_NAME

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#C8D6E5", size=12),
    legend=dict(bgcolor="rgba(255,255,255,0.04)",
                bordercolor="rgba(255,255,255,0.08)", borderwidth=1,
                font=dict(size=11)),
    margin=dict(l=16, r=16, t=44, b=16),
    hoverlabel=dict(bgcolor="rgba(15,30,60,0.95)",
                    bordercolor="rgba(46,134,171,0.5)",
                    font=dict(color="#E0E8F0", size=12)),
)


def _apply(fig: go.Figure, title: str = "", height: int = 340) -> go.Figure:
    fig.update_layout(**LAYOUT,
                      title=dict(text=title, font=dict(size=15, color="#FFFFFF"),
                                 x=0.01, xanchor="left"),
                      height=height)
    return fig


# ── Pie / Donut ───────────────────────────────────────────
def pie_chart(labels, values, title="", hole=0.42) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=hole,
        marker=dict(colors=CHART_COLORS,
                    line=dict(color="rgba(0,0,0,0.25)", width=2)),
        textinfo="label+percent", textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))
    return _apply(fig, title)


# ── Bar (vertical) ────────────────────────────────────────
def bar_chart(df, x, y, color=None, title="",
              xaxis_title="", yaxis_title="", barmode="group") -> go.Figure:
    fig = px.bar(df, x=x, y=y, color=color,
                 color_discrete_sequence=CHART_COLORS,
                 barmode=barmode)
    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        **LAYOUT,
        title=dict(text=title, font=dict(size=15, color="#FFFFFF"), x=0.01),
        height=340,
        xaxis=dict(title=xaxis_title, gridcolor="rgba(255,255,255,0.04)",
                   tickfont=dict(size=11)),
        yaxis=dict(title=yaxis_title, gridcolor="rgba(255,255,255,0.06)"),
    )
    return fig


# ── Horizontal Bar ────────────────────────────────────────
def horizontal_bar(labels, values, title="", color_idx=0) -> go.Figure:
    color = CHART_COLORS[color_idx % len(CHART_COLORS)]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=color, line=dict(width=0)),
        hovertemplate="<b>%{y}</b>: %{x}<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT, title=dict(text=title, font=dict(size=15, color="#FFFFFF"), x=0.01),
        height=max(280, 40 * len(labels) + 80),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    )
    return fig


# ── Grouped Bar ───────────────────────────────────────────
def grouped_bar(categories, series: dict, title="") -> go.Figure:
    """series = {'Publication': [10,5,...], 'Patent': [2,3,...]}"""
    fig = go.Figure()
    for i, (name, vals) in enumerate(series.items()):
        fig.add_trace(go.Bar(
            name=name, x=categories, y=vals,
            marker_color=CHART_COLORS[i % len(CHART_COLORS)],
            marker_line_width=0,
            hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y}}<extra></extra>",
        ))
    fig.update_layout(
        **LAYOUT, barmode="group",
        title=dict(text=title, font=dict(size=15, color="#FFFFFF"), x=0.01),
        height=360,
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    )
    return fig


# ── Stacked Bar ───────────────────────────────────────────
def stacked_bar(categories, series: dict, title="") -> go.Figure:
    fig = go.Figure()
    for i, (name, vals) in enumerate(series.items()):
        fig.add_trace(go.Bar(
            name=name, x=categories, y=vals,
            marker_color=CHART_COLORS[i % len(CHART_COLORS)],
            marker_line_width=0,
        ))
    fig.update_layout(
        **LAYOUT, barmode="stack",
        title=dict(text=title, font=dict(size=15, color="#FFFFFF"), x=0.01),
        height=360,
        xaxis=dict(tickfont=dict(size=10)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    )
    return fig


# ── Line Chart ────────────────────────────────────────────
def line_chart(df, x, y, title="", markers=True) -> go.Figure:
    if isinstance(y, list):
        fig = go.Figure()
        for i, col in enumerate(y):
            fig.add_trace(go.Scatter(
                x=df[x], y=df[col], name=col, mode="lines+markers",
                line=dict(color=CHART_COLORS[i % len(CHART_COLORS)], width=2.5),
                marker=dict(size=7),
                hovertemplate=f"<b>{col}</b><br>%{{x}}: %{{y}}<extra></extra>",
            ))
    else:
        c = CHART_COLORS[0]
        fig = go.Figure(go.Scatter(
            x=df[x], y=df[y], mode="lines+markers" if markers else "lines",
            line=dict(color=c, width=2.5),
            fill="tozeroy", fillcolor=c.replace(")", ",0.08)").replace("rgb", "rgba")
            if "rgb" in c else f"rgba(46,134,171,0.08)",
            marker=dict(size=7, color=c),
            hovertemplate="%{x}: <b>%{y}</b><extra></extra>",
        ))
    fig.update_layout(
        **LAYOUT,
        title=dict(text=title, font=dict(size=15, color="#FFFFFF"), x=0.01),
        height=340,
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    )
    return fig


# ── Area Chart ────────────────────────────────────────────
def area_chart(df, x, y_cols: list, title="") -> go.Figure:
    fig = go.Figure()
    for i, col in enumerate(y_cols):
        c = CHART_COLORS[i % len(CHART_COLORS)]
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], name=col,
            mode="lines", stackgroup="one",
            line=dict(color=c, width=1.5),
            fillcolor=c.replace(")", ",0.25)").replace("rgb", "rgba")
            if "rgb" in c else f"rgba(46,134,171,0.25)",
        ))
    fig.update_layout(
        **LAYOUT,
        title=dict(text=title, font=dict(size=15, color="#FFFFFF"), x=0.01),
        height=320,
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    )
    return fig


# ── Scatter ───────────────────────────────────────────────
def scatter_chart(df, x, y, size=None, color=None,
                  title="", xaxis_title="", yaxis_title="") -> go.Figure:
    fig = px.scatter(df, x=x, y=y, size=size, color=color,
                     color_discrete_sequence=CHART_COLORS,
                     size_max=22)
    fig.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color="rgba(255,255,255,0.3)")))
    fig.update_layout(
        **LAYOUT,
        title=dict(text=title, font=dict(size=15, color="#FFFFFF"), x=0.01),
        height=340,
        xaxis=dict(title=xaxis_title, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(title=yaxis_title, gridcolor="rgba(255,255,255,0.06)"),
    )
    return fig


# ── Monthly Trend ─────────────────────────────────────────
def monthly_trend_chart(entries: list[dict], title="Monthly Trend",
                        year_filter: int = None) -> go.Figure:
    if not entries:
        return go.Figure().update_layout(**LAYOUT, height=300)
    df = pd.DataFrame(entries)
    if "month" not in df.columns:
        return go.Figure().update_layout(**LAYOUT, height=300)
    if year_filter:
        df = df[df["year"] == year_filter]
    df["month_label"] = df["month"].map(MONTH_NUM_TO_NAME)
    pivot = df.groupby(["month", "month_label", "research_type"]).size().reset_index(name="count")
    pivot = pivot.sort_values("month")
    fig = go.Figure()
    for i, rtype in enumerate(sorted(df["research_type"].unique())):
        sub = pivot[pivot["research_type"] == rtype]
        c = CHART_COLORS[i % len(CHART_COLORS)]
        fig.add_trace(go.Scatter(
            x=sub["month_label"], y=sub["count"], name=rtype,
            mode="lines+markers",
            line=dict(color=c, width=2.5),
            marker=dict(size=8, color=c,
                        line=dict(color="rgba(0,0,0,0.3)", width=1)),
            hovertemplate=f"<b>{rtype}</b><br>%{{x}}: %{{y}}<extra></extra>",
        ))
    return _apply(fig, title, height=320)


# ── Department Comparison ─────────────────────────────────
def department_comparison_chart(dept_data: dict, title="") -> go.Figure:
    active = {k: v for k, v in dept_data.items() if v.get("total", 0) > 0}
    depts = list(active.keys())
    return grouped_bar(
        categories=[d[:20] for d in depts],
        series={
            "Journals":    [active[d].get("journals", 0)       for d in depts],
            "Conferences": [active[d].get("conferences", 0)    for d in depts],
            "Patents":     [active[d].get("patents", 0)        for d in depts],
            "Proposals":   [active[d].get("proposals", 0)      for d in depts],
        },
        title=title,
    )


# ── Gauge ─────────────────────────────────────────────────
def gauge_chart(value, max_val, title="", unit="") -> go.Figure:
    pct = min(value / max_val * 100, 100) if max_val else 0
    color = "#2ECC71" if pct >= 75 else ("#F39C12" if pct >= 40 else "#E74C3C")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 13, "color": "#C8D6E5"}},
        number={"suffix": unit, "font": {"color": "#FFFFFF", "size": 28}},
        gauge={
            "axis": {"range": [0, max_val], "tickcolor": "#7F8C8D",
                     "tickfont": {"size": 10}},
            "bar": {"color": color, "thickness": 0.7},
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": "rgba(255,255,255,0.08)",
            "steps": [
                {"range": [0, max_val*0.4],  "color": "rgba(231,76,60,0.1)"},
                {"range": [max_val*0.4, max_val*0.75], "color": "rgba(243,156,18,0.1)"},
                {"range": [max_val*0.75, max_val], "color": "rgba(46,204,113,0.1)"},
            ],
        },
    ))
    return _apply(fig, height=220)


# ── Yearly Comparison Bar ─────────────────────────────────
def yearly_comparison(entries: list[dict], title="Year-over-Year") -> go.Figure:
    if not entries:
        return go.Figure().update_layout(**LAYOUT, height=300)
    df = pd.DataFrame(entries)
    if "year" not in df.columns:
        return go.Figure().update_layout(**LAYOUT, height=300)
    pivot = df.groupby(["year", "research_type"]).size().reset_index(name="count")
    years = sorted(pivot["year"].unique())
    types = sorted(pivot["research_type"].unique())
    series = {}
    for t in types:
        sub = pivot[pivot["research_type"] == t].set_index("year")
        series[t] = [int(sub.loc[y, "count"]) if y in sub.index else 0 for y in years]
    return grouped_bar([str(y) for y in years], series, title)
