"""
pages/hod_dashboard.py - Enhanced HoD Dashboard
"""
from __future__ import annotations
import streamlit as st
import pandas as pd

from database.queries import (
    fetch_department_entries, fetch_profiles_by_department,
    get_department_stats, fetch_active_reminders,
)
from services.auth_service import get_current_profile
from services.export_service import entries_to_dataframe, to_csv_bytes, to_excel_bytes, to_pdf_bytes
from components.ui import metric_card, page_header, section_header, reminder_card, status_badge, render_faculty_profile_card
from utils.charts import (
    pie_chart, horizontal_bar,
    grouped_bar, stacked_bar, yearly_comparison,
)
from utils.helpers import get_years_list, num_to_month_name
from config import RESEARCH_TYPES, MONTHS


def render_hod_dashboard():
    profile = get_current_profile()
    dept    = profile.get("department", "")

    page_header("HoD Dashboard", f"Department of {dept}", "")

    reminders = fetch_active_reminders("hod")
    if reminders:
        with st.expander(f"🔔 {len(reminders)} Reminder(s)"):
            for r in reminders: reminder_card(r)

    stats = get_department_stats(dept)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: metric_card("Total Entries", stats["total"], "📄", color="#2E86AB")
    with c2: metric_card("Journals", stats["journals"], "📓", color="#3498DB")
    with c3: metric_card("Conferences", stats["conferences"], "🎙️", color="#9B59B6")
    with c4: metric_card("Patents", stats["patents"], "💡", color="#F18F01")
    with c5: metric_card("Research Proposals", stats["proposals"], "📋", color="#E74C3C")
    with c6: metric_card("Active Researchers", stats["active_researchers"], "👥", color="#2ECC71")

    st.markdown("<br>", unsafe_allow_html=True)
    tab_ov, tab_entries, tab_fac, tab_export = st.tabs(
        ["📊 Overview", "📋 Entries", "👥 Faculty", "⬇ Export"])

    # ── OVERVIEW ─────────────────────────────────────────
    with tab_ov:
        all_e = fetch_department_entries(dept)
        if not all_e:
            st.info("No data yet for this department.")
        else:
            r1c1, r1c2 = st.columns(2)
            with r1c1:
                st.plotly_chart(pie_chart(
                    ["Journal", "Conference", "Patent", "Research Proposal"],
                    [stats["journals"], stats["conferences"], stats["patents"], stats["proposals"]],
                    "Research Type Distribution"), use_container_width=True)
            with r1c2:
                # Indexing distribution for journals/conferences
                pubs = [e for e in all_e
                        if e["research_type"] in ("Journal", "Conference") and e.get("indexing")]
                if pubs:
                    idx_cnt = {}
                    for e in pubs:
                        i = e["indexing"]; idx_cnt[i] = idx_cnt.get(i, 0) + 1
                    st.plotly_chart(pie_chart(list(idx_cnt.keys()), list(idx_cnt.values()),
                                              "Publication Indexing"), use_container_width=True)
                else:
                    st.info("No indexed publications yet.")

            # Faculty performance grouped bar
            section_header("Faculty Performance", "🏆")
            faculty   = fetch_profiles_by_department(dept)
            fac_names = []
            jour_v, conf_v, pats_v, props_v = [], [], [], []
            for f in faculty:
                fid  = f["id"]
                fe   = [e for e in all_e if e["faculty_id"] == fid]
                if fe:
                    fac_names.append(f.get("full_name","")[:20])
                    jour_v.append(sum(1 for e in fe if e["research_type"]=="Journal"))
                    conf_v.append(sum(1 for e in fe if e["research_type"]=="Conference"))
                    pats_v.append(sum(1 for e in fe if e["research_type"]=="Patent"))
                    props_v.append(sum(1 for e in fe if e["research_type"]=="Research Proposal"))

            if fac_names:
                # Sort by total desc
                combined = sorted(zip(fac_names, jour_v, conf_v, pats_v, props_v),
                                  key=lambda x: x[1]+x[2]+x[3]+x[4], reverse=True)
                fac_names, jour_v, conf_v, pats_v, props_v = zip(*combined)
                st.plotly_chart(grouped_bar(
                    list(fac_names),
                    {"Journals": list(jour_v),
                     "Conferences": list(conf_v),
                     "Patents":       list(pats_v),
                     "Proposals":     list(props_v)},
                    "Faculty Research Output (by Type)"), use_container_width=True)

            # Year-wise research trend for department
            section_header("Year-wise Research Trend", "📅")
            st.plotly_chart(yearly_comparison(all_e, "Department Year-wise Research Output"),
                            use_container_width=True)

    # ── ENTRIES ──────────────────────────────────────────
    with tab_entries:
        fc1, fc2, fc3 = st.columns(3)
        with fc1: f_type  = st.selectbox("Type", ["All"]+RESEARCH_TYPES, key="hod_ft")
        with fc2: f_year  = st.selectbox("Year", ["All"]+[str(y) for y in get_years_list()], key="hod_fy")
        with fc3: f_srch  = st.text_input("🔍 Search", key="hod_fs")

        filters = {}
        if f_type != "All": filters["research_type"] = f_type
        if f_year != "All": filters["year"] = int(f_year)
        entries = fetch_department_entries(dept, filters)
        if f_srch:
            entries = [e for e in entries if f_srch.lower() in e.get("title","").lower()]

        st.markdown(f"**{len(entries)} record(s)**")
        if entries:
            _render_table(entries, show_faculty=True)

    # ── FACULTY ──────────────────────────────────────────
    with tab_fac:
        section_header("Faculty Summary", "👥")
        faculty  = fetch_profiles_by_department(dept)
        all_e    = fetch_department_entries(dept)
        rows = []
        for f in faculty:
            fid = f["id"]
            fe  = [e for e in all_e if e["faculty_id"] == fid]
            rows.append({
                "Name":         f.get("full_name",""),
                "Email":        f.get("email",""),
                "Journals":     sum(1 for e in fe if e["research_type"]=="Journal"),
                "Conferences":  sum(1 for e in fe if e["research_type"]=="Conference"),
                "Patents":      sum(1 for e in fe if e["research_type"]=="Patent"),
                "Proposals":    sum(1 for e in fe if e["research_type"]=="Research Proposal"),
                "Total":        len(fe),
                "Status":       "✅ Active" if f.get("is_active",True) else "🔴 Inactive",
            })
        if rows:
            df = pd.DataFrame(rows).sort_values("Total", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True,
                         column_config={
                             "Total": st.column_config.ProgressColumn(
                                 "Total", max_value=int(df["Total"].max() or 1))
                         })
            
            st.markdown("<br>", unsafe_allow_html=True)
            section_header("Faculty Profiles Directory", "📖")
            for f in faculty:
                if f.get("role") in ["faculty", "hod", "rd_coordinator"]:
                    fid = f["id"]
                    fe  = [e for e in all_e if e["faculty_id"] == fid]
                    metrics = {
                        "Journals": sum(1 for e in fe if e["research_type"]=="Journal"),
                        "Conferences": sum(1 for e in fe if e["research_type"]=="Conference"),
                        "Patents": sum(1 for e in fe if e["research_type"]=="Patent"),
                        "Proposals": sum(1 for e in fe if e["research_type"]=="Research Proposal")
                    }
                    render_faculty_profile_card(f, metrics)
        else:
            st.info("No faculty found.")

    # ── EXPORT ───────────────────────────────────────────
    with tab_export:
        section_header("Export Department Data", "⬇")
        all_e = fetch_department_entries(dept)
        ey, et = st.columns(2)
        with ey: ex_yr = st.selectbox("Year", ["All"]+[str(y) for y in get_years_list()], key="hod_ey")
        with et: ex_ty = st.selectbox("Type", ["All"]+RESEARCH_TYPES, key="hod_et")
        exp_e = [e for e in all_e
                 if (ex_yr=="All" or str(e.get("year",""))==ex_yr)
                 and (ex_ty=="All" or e.get("research_type")==ex_ty)]
        df_ex = entries_to_dataframe(exp_e)
        st.markdown(f"**{len(exp_e)} records**")
        ec1, ec2 = st.columns(2)
        with ec1:
            st.download_button("⬇ CSV", to_csv_bytes(df_ex),
                               f"{dept[:20]}_research.csv","text/csv", use_container_width=True)
        with ec2:
            st.download_button("⬇ Excel", to_excel_bytes(df_ex, dept),
                               f"{dept[:20]}_research.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        with st.expander("📋 Preview"):
            st.dataframe(df_ex.head(20), use_container_width=True, hide_index=True)


# ── TABLE with Download Option ─────────────────────────────────────────
def _render_table(entries, show_faculty=False):
    from datetime import date
    st.markdown("""
    <style>
    .ov-hdr{font-size:.67rem;font-weight:700;color:#64748B;text-transform:uppercase;
            letter-spacing:.07em;padding-bottom:3px;}
    .ov-title{font-size:.88rem;font-weight:600;color:#1E293B;line-height:1.3;}
    .ov-sub{font-size:.76rem;color:#475569;}
    .ov-chip{background:#F1F5F9;border-radius:20px;padding:2px 9px;
             font-size:.76rem;color:#475569;display:inline-block;}
    </style>
    """, unsafe_allow_html=True)

    # Column layout: Title | Type | Venue | Indexing | Status | Date | Doc
    CW = [3.4, 1.2, 1.8, 1.0, 1.3, 1.0, 0.5]
    hdrs = ["Title", "Type", "Journal/Office", "Indexing", "Status", "Date", "Doc"]
    if show_faculty:
        CW = [1.5] + CW
        hdrs = ["Faculty"] + hdrs

    hcols = st.columns(CW)
    for hc, hl in zip(hcols, hdrs):
        hc.markdown(f"<div class='ov-hdr'>{hl}</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:2px 0 6px 0;border-color:#E2E8F0;'>", unsafe_allow_html=True)

    for i, e in enumerate(entries):
        title = (e.get("title") or "")
        rtype = e.get("research_type", "")
        venue = (e.get("journal_or_patent_office") or "")[:28]
        idx   = e.get("indexing") or "—"
        doc   = e.get("document_url")
        # Smart date: for patents use publication_date, else year/month
        try:
            if rtype == "Patent":
                pdate = e.get("publication_date") or e.get("filing_date") or e.get("submission_date")
                disp_date = date.fromisoformat(str(pdate)[:10]).strftime("%b %Y") if pdate else "—"
            else:
                yr = e.get("year"); mo = e.get("month")
                disp_date = date(int(yr), int(mo or 1), 1).strftime("%b %Y") if yr else "—"
        except Exception:
            disp_date = str(e.get("year", "—"))

        rcols = st.columns(CW)
        col_offset = 0
        if show_faculty:
            fac = e.get("profiles", {})
            fname = fac.get("full_name", "—") if isinstance(fac, dict) else "—"
            rcols[0].markdown(f"<div class='ov-sub'>{fname}</div>", unsafe_allow_html=True)
            col_offset = 1

        rcols[col_offset+0].markdown(
            f"<div class='ov-title'>{title[:50]}{'…' if len(title)>50 else ''}</div>",
            unsafe_allow_html=True)
        rcols[col_offset+1].markdown(
            f"<span class='type-badge type-{rtype.lower().replace(' ','-')}'>{rtype}</span>",
            unsafe_allow_html=True)
        rcols[col_offset+2].markdown(f"<div class='ov-sub'>{venue}</div>", unsafe_allow_html=True)
        rcols[col_offset+3].markdown(f"<div class='ov-sub'>{idx}</div>", unsafe_allow_html=True)
        rcols[col_offset+4].markdown(status_badge(e.get("status", "")), unsafe_allow_html=True)
        rcols[col_offset+5].markdown(f"<span class='ov-chip'>{disp_date}</span>", unsafe_allow_html=True)
        if doc:
            rcols[col_offset+6].markdown(
                f"<a href='{doc}' target='_blank' style='font-size:1.1rem;'>&#11015;&#65039;</a>",
                unsafe_allow_html=True)
        else:
            rcols[col_offset+6].markdown("—")

        if i < len(entries) - 1:
            st.markdown("<hr style='margin:4px 0;border-color:#E2E8F0;opacity:1;'>",
                        unsafe_allow_html=True)

